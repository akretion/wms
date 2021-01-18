
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import wraps
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
    def __init__(self, state, data, message_name):
        super().__init__(state, data)
        self.message_name = message_name

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
            message = getattr(instance.msg_store, e.message_name)()
            return instance._response(
                state=e.state,
                data=e.data,
                message=message
            )
        except MessageBasedError as e:
            return instance._response(
                state=e.state,
                data=e.data,
                message=e.message
            )

    return decorated_response

class ClusterBatchPicking(Component):
    _inherit = "base.shopfloor.process"
    _name = "shopfloor.cluster.batch_picking"
    _usage = "cluster_batch_picking"
    _description = __doc__

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

    def _get_batch(self, picking_batch_id):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            raise BatchDoesNotExistError

    def _get_move_line(self, move_line_id):
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            raise OperationNotFoundError(
                func_args={"batch": batch}
            )

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
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")

        return self._response_for_scan_products(move_lines)

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
        }

    def find_batch(self):
        return self._response_schema(next_states={"confirm_start"})

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
                "show_move_lines_by_location",
            }
        )

    @property
    def _schema_for_batch_details(self):
        return self.schemas.picking_batch(with_pickings=True)
