
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import wraps, reduce
from odoo import _, fields
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float

class ScenarioError(Exception):
    def __init__(self, response):
        super().__init__("")
        self.response = response

class StateBasedError(Exception):
    def __init__(self, state, data):
        super().__init__("")
        self.state = state
        self.data = data

class MessageNameBasedError(StateBasedError):
    def __init__(self, state, data, message_name, **kw):
        super().__init__(state, data)
        self.message_name = message_name
        self.kw = kw

class MessageBasedError(StateBasedError):
    def __init__(self, state, data, message):
        super().__init__(state, data)
        self.message = message

class BatchDoesNotExistError(Exception):
    pass

class OperationNotFoundError(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="operation_not_found")

class BarcodeNotFoundError(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="barcode_not_found")

class UnableToPickMoreError(MessageNameBasedError):
    def __init__(self, state, data, **kw):
        super().__init__(state, data, message_name="unable_to_pick_more", **kw)

class DestLocationNotAllowed(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="dest_location_not_allowed")

class TooMuchProductInCommandError(MessageBasedError):
    def __init__(self, state, data):
        message = {
            "message_type": "error",
            "body": "Too much product in command",
        }
        super().__init__(state, data, message)

def response_decorator(called_func):

    @wraps(called_func)
    def decorated_response(*args, **kwargs):
        instance = args[0]
        try:
            return called_func(*args, **kwargs)
        except BatchDoesNotExistError:
            return instance._response_batch_does_not_exist()
        except MessageNameBasedError as e:
            message = getattr(instance.msg_store, e.message_name)(**(e.kw))
            return instance._response(
                next_state=e.state,
                data=e.data,
                message=message
            )
        except MessageBasedError as e:
            return instance._response(
                next_state=e.state,
                data=e.data,
                message=e.message
            )

    return decorated_response

class ClusterBatchPicking(Component):
    _inherit = "base.shopfloor.process"
    _name = "shopfloor.cluster.batch_picking"
    _usage = "cluster_batch_picking"
    _description = __doc__

    @staticmethod
    def _sort_key_lines(line):
        return (
            line.shopfloor_priority or 10,
            line.location_id.shopfloor_picking_sequence or "",
            line.location_id.name,
            -int(line.move_id.priority or 1),
            line.move_id.date_expected,
            line.move_id.sequence,
            line.move_id.id,
            line.id,
        )

    def _get_lines_to_pick(self, move_lines):
        return move_lines.filtered(
            lambda l: (
                l.state in ("assigned", "partially_available")
                # On 'StockPicking.action_assign()', result_package_id is set to
                # the same package as 'package_id'. Here, we need to exclude lines
                # that were already put into a bin, i.e. the destination package
                # is different.
                and (not l.result_package_id or l.result_package_id == l.package_id)
                and (l.picking_id.location_dest_id == l.location_dest_id)
            ),
        ).sorted(key=self._sort_key_lines)


    def _next_line_for_pick(self, move_lines):
        remaining_lines = self._get_lines_to_pick(move_lines)
        return fields.first(remaining_lines)

    def _batch_filter(self, batch):
        if not batch.picking_ids:
            return False
        return batch.picking_ids.filtered(self._batch_picking_filter)

    def _batch_picking_filter(self, picking):
        # Picking type guard
        if picking.picking_type_id not in self.picking_types:
            return False
        # Include done/cancel because we want to be able to work on the
        # batch even if some pickings are done/canceled. They'll should be
        # ignored later.
        # When the batch is already in progress, we do not care
        # about state of the pickings, because we want to be able
        # to recover it in any case, even if, for instance, a stock
        # error changed a picking to unavailable after the user
        # started to work on the batch.
        return picking.batch_id.state == "in_progress" or picking.state in (
            "assigned",
            "done",
            "cancel",
        )

    def _create_data_for_scan_products(
        self,
        move_lines,
        batch,
    ):
        picking_destination = {}
        for picking in batch.picking_ids:
            picking_destination[picking.id] = {
            }

            suggested_location_dest = []
            suggested_package_dest = []

            for line_in_picking in picking.move_line_ids:
                if line_in_picking.location_dest_id and line_in_picking.location_dest_id != picking.location_dest_id:
                    suggested_location_dest.append(
                        self.data.location(line_in_picking.mapped("location_dest_id"))
                    )
                if line_in_picking.result_package_id:
                    suggested_package_dest.append(
                        self.data.package(line_in_picking.mapped("result_package_id"))
                    )

            suggested_package_dest = reduce(lambda l, x: l.append(x) or l if x not in l else l, suggested_package_dest, [])
            suggested_location_dest = reduce(lambda l, x: l.append(x) or l if x not in l else l, suggested_location_dest, [])

            picking_destination[picking.id]["suggested_package_dest"] = suggested_package_dest
            picking_destination[picking.id]["suggested_location_dest"] = suggested_location_dest

        move_lines_data = self.data.move_lines(move_lines, with_picking=True, with_packaging=True)
        for line in move_lines_data:
            picking = line["picking"]
            line.update(picking_destination[picking["id"]])

        return {
            "move_lines": move_lines_data,
            "id": batch.id,
        }

    def _response_for_scan_products(self, move_lines, batch, message=None):
        next_line = self._next_line_for_pick(move_lines)

        if not next_line:
            return self.prepare_unload(batch.id)

        return self._response(
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch),
            message=message,
        )

    def _response_batch_does_not_exist(self):
        return self._response_for_start(message=self.msg_store.record_not_found())

    def _batch_picking_base_search_domain(self):
        return [
            "|",
            "&",
            ("user_id", "=", False),
            ("state", "=", "draft"),
            "&",
            ("user_id", "=", self.env.user.id),
            ("state", "in", ("draft", "in_progress")),
        ]

    def _batch_picking_search(self, name_fragment=None, batch_ids=None):
        domain = self._batch_picking_base_search_domain()
        if name_fragment:
            domain = expression.AND([domain, [("name", "ilike", name_fragment)]])
        if batch_ids:
            domain = expression.AND([domain, [("id", "in", batch_ids)]])
        records = self.env["stock.picking.batch"].search(domain, order="id asc")
        records = records.filtered(self._batch_filter)
        return records

    def _select_a_picking_batch(self, batches):
        # look for in progress + assigned to self first
        candidates = batches.filtered(
            lambda batch: batch.state == "in_progress"
            and batch.user_id == self.env.user
        )
        if candidates:
            return candidates[0]
        # then look for draft assigned to self
        candidates = batches.filtered(lambda batch: batch.user_id == self.env.user)
        if candidates:
            batch = candidates[0]
            batch.write({"state": "in_progress"})
            return batch
        # finally take any batch that search could return
        if batches:
            batch = batches[0]
            batch.write({"user_id": self.env.uid, "state": "in_progress"})
            return batch
        return self.env["stock.picking.batch"]

    def _set_quantity_for_move_line(self, move_lines, batch, product, move_line, quantity_to_set, next_state, data):
        if product and move_line.product_id == product:
            if quantity_to_set > move_line.product_uom_qty:
                raise TooMuchProductInCommandError(
                    state=next_state,
                    data=data,
                )

            move_line.qty_done = quantity_to_set

            return self._response_for_scan_products(move_lines, batch)
        else:
            raise BarcodeNotFoundError(
                state=next_state,
                data=data,
            )

    def _get_batch(self, picking_batch_id):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            raise BatchDoesNotExistError
        return batch

    def _get_move_line(self, move_line_id, next_state, data):
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            raise OperationNotFoundError(
                state=next_state,
                data=data,
            )
        return move_line

    @response_decorator
    def find_batch(self):
        """Find a picking batch to work on and start it

        Usually the starting point of the scenario.

        Business rules to find a batch, try in order:

        a. Find a batch in progress assigned to the current user
        b. Find a draft batch assigned to the current user:
          1. set it to 'in progress'
        c. Find an unassigned draft batch:
          1. assign batch to the current user
          2. set it to 'in progress'

        Transitions:
        * confirm_start: when it could find a batch
        * start: when no batch is available
        """
        batches = self._batch_picking_search()
        selected = self._select_a_picking_batch(batches)
        if selected:
            return self._response(
                next_state="confirm_start",
                data=self.data.picking_batch(selected, with_pickings=True),
            )
        else:
            return self._response(
                next_state="start",
                message={
                    "message_type": "info",
                    "body": _("No more work to do, please create a new batch transfer"),
                },
            )

    @response_decorator
    def scan_product(self, picking_batch_id, move_line_id, barcode):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id,
            next_state="scan_products",
            data=self._create_data_for_scan_products(
                move_lines,
                batch,
            ),
        )

        search = self.actions_for("search")

        product = search.product_from_scan(barcode)
        quantity_to_set = move_line.qty_done + 1

        return self._set_quantity_for_move_line(
            move_lines,
            batch,
            product,
            move_line,
            quantity_to_set,
            next_state="scan_products",
            data=self._create_data_for_scan_products(
                move_lines,
                batch,
            ),
        )

    @response_decorator
    def confirm_start(self, picking_batch_id):
        """User confirms they start a batch

        Should have no effect in odoo besides logging and routing the user to
        the next action. The next action is "start_line" with data about the
        line to pick.

        Transitions:
        * start_line: when the batch has at least one line without destination
          package
        * start: if the condition above is wrong (rare case of race condition...)
        """
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")

        return self._response_for_scan_products(move_lines, batch)

    @response_decorator
    def set_quantity(self, picking_batch_id, move_line_id, barcode, qty):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id,
            next_state="scan_products",
            data=self._create_data_for_scan_products(
                move_lines,
                batch,
            ),
        )

        search = self.actions_for("search")

        product = search.product_from_scan(barcode)

        return self._set_quantity_for_move_line(
            move_lines,
            batch,
            product,
            move_line,
            qty,
            next_state="scan_products",
            data=self._create_data_for_scan_products(
                move_lines,
                batch,
            ),
        )

    @response_decorator
    def set_destination(self, picking_batch_id, move_line_id, barcode, qty):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(move_line_id, next_state="scan_products", data="move_lines")

        search = self.actions_for("search")

        location_dest = search.location_from_scan(barcode)
        bin_package = search.package_from_scan(barcode)

        if not location_dest and not bin_package:
            raise BarcodeNotFoundError(
                state="scan_products",
                data=self._create_data_for_scan_products(
                    move_lines,
                    batch,
                ),
            )

        new_line, qty_check = move_line._split_qty_to_be_done(qty)

        if qty_check == "greater":
            raise UnableToPickMoreError(
                state="scan_products",
                data=self._create_data_for_scan_products(
                    move_lines,
                    batch,
                ),
                quantity=move_line.product_uom_qty,
            )

        if location_dest:
            if not location_dest.is_sublocation_of(
                move_line.picking_id.location_dest_id
            ):
                raise UnableToPickMoreError(
                    state="scan_products",
                    data=self._create_data_for_scan_products(
                        move_lines,
                        batch,
                    ),
                )

            move_line.write({"qty_done": qty, "location_dest_id": location_dest.id})
            move_line.shopfloor_checkout_done = True

            return self._response_for_scan_products(
                move_lines,
                batch,
                message=self.msg_store.x_units_put_in_location(
                    move_line.qty_done, move_line.product_id, location_dest
                ),
            )

        if bin_package:
            move_line.write({"qty_done": qty, "result_package_id": bin_package.id})
            move_line.shopfloor_checkout_done = True

            return self._response_for_scan_products(
                move_lines,
                batch,
                message=self.msg_store.x_units_put_in_package(
                    move_line.qty_done, move_line.product_id, move_line.result_package_id
                ),
            )

    @response_decorator
    def prepare_unload(self, picking_batch_id):
        """Initiate the unloading phase of the scenario

        It goes to different screens depending if all the move lines have
        the same destination or not.

        Transitions:
        * unload_all: when all lines go to the same destination
        * unload_single: when lines have different destinations
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if self._are_all_dest_location_same(batch):
            return self._response_for_unload_all(batch)
        else:
            # the lines have different destinations
            return self._unload_next_package(batch)

    @response_decorator
    def cancel_line(self, picking_batch_id, move_line_id):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(move_line_id, next_state="scan_products", data="move_lines")

        move_line.qty_done = 0
        move_line.shopfloor_checkout_done = False
        move_line.result_package_id = None
        move_line.location_dest_id = move_line.picking_id.location_dest_id

        return self._response_for_scan_products(
            move_lines,
            batch,
        )


class ShopfloorClusterBatchPickingValidator(Component):
    """Validators for the Cluster Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.cluster_batch_picking.validator"
    _usage = "cluster_batch_picking.validator"

    def find_batch(self):
        return {}

    def confirm_start(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def set_quantity(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def scan_product(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_destination(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def cancel_line(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

class ShopfloorClusterPickingValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.cluster_batch_picking.validator.response"
    _usage = "cluster_batch_picking.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "confirm_start": self._schema_for_batch_details,
            "unload_all": self._schema_for_batch_details,
            "unload_single": self._schema_for_batch_details,
            "scan_products": self._schema_for_move_lines_details,
            "start": {},
        }

    def find_batch(self):
        return self._response_schema(next_states={"confirm_start"})

    def set_quantity(self):
        return self._response_schema(
            next_states={
                "scan_products",
            }
        )

    def set_destination(self):
        return self._response_schema(
            next_states={
                "unload_all",
                "unload_single",
                "scan_products",
            }
        )

    def scan_product(self):
        return self._response_schema(
            next_states={
                "scan_products",
            }
        )

    def confirm_start(self):
        return self._response_schema(
            next_states={
                # we reopen a batch already started where all the lines were
                # already picked and have to be unloaded to the same
                # destination
                "unload_all",
                # we reopen a batch already started where all the lines were
                # already picked and have to be unloaded to the different
                # destinations
                "unload_single",
                "scan_products",
            }
        )

    def cancel_line(self):
        return self._response_schema(
            next_states={"scan_products"}
        )

    @property
    def _schema_for_move_lines_details(self):
        return {
            "move_lines": self.schemas._schema_list_of(self.schemas.move_line(with_packaging=True, with_picking=True)),
            "id": {"required": True, "type": "integer"},
        }

    @property
    def _schema_for_batch_details(self):
        return self.schemas.picking_batch(with_pickings=True)
