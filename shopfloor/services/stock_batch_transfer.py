# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    BarcodeNotFoundError,
    DestLocationNotAllowed,
    LocationNotFound,
    OperationNotFoundError,
    ScenarioError,
    response_decorator,
)


class StockBatchTransfer(Component):
    """
    Methods for Input Stock Transfer Process

    Allows the transfer of products in input location
    and input sublocation to their proper stock location
    This is the 2nd step in 2-step reception.

    Expected:

    * Input sublocation/Input location scanned once
    * User should be led on an optimal path through the warehouse
    * Destination scanned after each product placement on a stock location
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.stock.batch.transfer"
    _usage = "stock_batch_transfer"
    _description = __doc__

    def _location_search_domain(self):
        return [("shopfloor_is_stock_transfer_input_location", "=", True)]

    def _move_lines_search_domain(self, location_id):
        return [
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.state", "=", "assigned"),
            ("location_id.id", "=", location_id),
            ("product_uom_qty", ">", 0),
        ]

    def _get_data_for_scan_products(
        self,
        current_source_location_id,
        product_barcode=None,
        location_barcode=None,
        dest_location_id=None,
    ):
        search = self._actions_for("search")
        current_source_location = self.env["stock.location"].browse(
            current_source_location_id
        )
        move_lines_children = self.env["stock.move.line"].search(
            self._move_lines_search_domain(current_source_location.id)
        )

        dest_location = None
        product_move_lines = []
        product = None
        location = None
        if dest_location_id:
            dest_location = self.env["stock.location"].browse(dest_location_id)

        if product_barcode:
            product_move_lines = [
                line
                for line in move_lines_children
                if line.product_id.barcode == product_barcode
                or product_barcode
                in [barcode.name for barcode in line.product_id.mapped("barcode_ids")]
            ]
            product = search.product_from_scan(product_barcode)

        if location_barcode:
            location = search.location_from_scan(location_barcode)
            print(location_barcode)

        return (
            current_source_location,
            move_lines_children,
            product_move_lines,
            location,
            dest_location,
            product,
        )

    def _create_data_for_scan_products(
        self,
        all_move_lines,
        current_source_location_id=None,
        selected_location_id=None,
        selected_product_barcode_ids=None,
        move_lines_done=None,
    ):
        data = {
            "move_lines": self.data.move_lines(all_move_lines, with_picking=True),
            "id": current_source_location_id,
            "selected_location": selected_location_id,
            "move_lines_done": move_lines_done,
        }

        if selected_product_barcode_ids:
            data.update(
                {"selected_product": selected_product_barcode_ids.mapped("name")}
            )

        return data

    def _process_pickings(self, all_move_lines):
        picking_ids = {line.picking_id for line in all_move_lines}

        for picking in picking_ids:
            move_lines = picking.mapped("move_line_ids")

            if all([line.shopfloor_checkout_done for line in move_lines]):
                picking.action_done()

    def _create_response_for_scan_products(
        self,
        all_move_lines,
        current_source_location_id,
        selected_location_id=None,
        selected_product_barcode_ids=None,
        message=None,
        move_lines_done=None,
    ):
        data = self._create_data_for_scan_products(
            all_move_lines,
            current_source_location_id,
            selected_location_id,
            selected_product_barcode_ids,
            move_lines_done,
        )

        if all([line.shopfloor_checkout_done for line in all_move_lines]):
            try:
                self._process_pickings(all_move_lines)

                domain = self._location_search_domain()
                records = self.env["stock.location"].search(domain)
                data = self.data_detail.locations_detail(records)
                return self._response(
                    next_state="start",
                    data={"input_locations": data},
                    message={
                        "message_type": "success",
                        "body": _("Transfer completed"),
                    },
                )
            except Exception:
                raise ScenarioError(
                    response=self._response(
                        next_state="scan_products",
                        data=data,
                        message={
                            "message_type": "error",
                            "body": _("There was an error while ending the picking"),
                        },
                    )
                )

        return self._response(next_state="scan_products", data=data, message=message,)

    def list_input_location(self):
        domain = self._location_search_domain()
        records = self.env["stock.location"].search(domain)
        data = self.data_detail.locations_detail(records)

        data = [
            location
            for location in data
            if not all(
                [
                    line.shopfloor_checkout_done
                    for line in self.env["stock.move.line"].search(
                        self._move_lines_search_domain(location["id"])
                    )
                ]
            )
        ]
        return self._response(next_state="start", data={"input_locations": data})

    def _set_product_move_line_quantity(
        self,
        current_source_location,
        product_move_lines,
        qty,
        move_lines_children=None,
        dest_location_id=None,
        product=None,
    ):
        quantity_to_add = qty
        move_line_index = 0

        while quantity_to_add > 0 and move_line_index < len(product_move_lines):
            current_move_line = product_move_lines[move_line_index]
            quantity_possible_to_add = (
                current_move_line.product_uom_qty - current_move_line.qty_done
            )
            quantity_added_to_move_line = min(quantity_possible_to_add, quantity_to_add)
            current_move_line.qty_done += quantity_added_to_move_line
            quantity_to_add -= quantity_added_to_move_line

            if current_move_line.qty_done == current_move_line.product_uom_qty:
                move_line_index += 1

        if quantity_to_add > 0:
            move_lines_data = self._create_data_for_scan_products(
                move_lines_children,
                current_source_location.id,
                selected_location_id=dest_location_id,
                selected_product_barcode_ids=product.barcode_ids,
            )
            raise OperationNotFoundError(
                state="scan_products", data=move_lines_data,
            )

    def _reset_product_quantity(
        self, product_move_lines,
    ):
        for line in product_move_lines:
            if not line.shopfloor_checkout_done:
                line.qty_done = 0

    def _put_move_lines_in_destination(
        self, product_move_lines, destination,
    ):
        quantity_stored = 0
        lines_done = []

        for line in product_move_lines:
            quantity_stored += line.qty_done
            if line.qty_done == line.product_uom_qty:
                line.write({"location_dest_id": destination.id})
                if not line.shopfloor_checkout_done:
                    lines_done += [line.id]
                line.shopfloor_checkout_done = True
            elif line.qty_done < line.product_uom_qty:
                line._split_qty_to_be_done(line.qty_done)

                line.write({"location_dest_id": destination.id})
                lines_done += [line.id]
                line.shopfloor_checkout_done = True

        return (
            {
                "message_type": "success",
                "body": _("{} {} put in {}").format(
                    quantity_stored,
                    product_move_lines[0].product_id.name,
                    destination.name,
                ),
            },
            lines_done,
        )

    @response_decorator
    def scan_location(self, barcode):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)

        move_lines_children = self.env["stock.move.line"].search(
            self._move_lines_search_domain(location.id)
        )

        return self._create_response_for_scan_products(
            move_lines_children,
            location.id,
            message={
                "message_type": "success",
                "body": _("{} location selected".format(location.display_name)),
            },
        )

    @response_decorator
    def set_current_location(self, barcode, current_source_location_id):
        (
            current_source_location,
            move_lines_children,
            _,
            location,
            _,
            _,
        ) = self._get_data_for_scan_products(
            current_source_location_id=current_source_location_id,
            location_barcode=barcode,
        )

        # We check if the current location is a destination
        # location of at least one of the move
        # of the current_source_location
        valid_location = False
        for line in move_lines_children:
            if line.location_dest_id.id == location.id:
                valid_location = True
                break

        # If it's not we tell the user that he can't chose this destination
        if not valid_location:
            data = self._create_data_for_scan_products(
                move_lines_children, current_source_location.id,
            )
            raise DestLocationNotAllowed(
                state="scan_products", data=data,
            )

        return self._create_response_for_scan_products(
            move_lines_children, current_source_location.id, location.id,
        )

    @response_decorator
    def drop_product_to_location(
        self, barcode, current_source_location_id, dest_location_id
    ):
        (
            current_source_location,
            move_lines_children,
            product_move_lines,
            _,
            dest_location,
            product,
        ) = self._get_data_for_scan_products(
            current_source_location_id=current_source_location_id,
            dest_location_id=dest_location_id,
            product_barcode=barcode,
        )

        if not dest_location or not current_source_location:
            data = self._create_data_for_scan_products(
                move_lines_children, current_source_location.id, dest_location.id,
            )
            raise LocationNotFound(
                state="scan_products", data=data,
            )

        if len(product_move_lines) == 0:
            data = self._create_data_for_scan_products(
                move_lines_children, current_source_location.id, dest_location.id,
            )
            raise BarcodeNotFoundError(
                state="scan_products", data=data,
            )

        self._set_product_move_line_quantity(
            current_source_location,
            product_move_lines,
            1,
            move_lines_children=move_lines_children,
            dest_location_id=dest_location.id,
            product=product,
        )

        return self._create_response_for_scan_products(
            move_lines_children,
            current_source_location.id,
            dest_location.id,
            product.barcode_ids,
        )

    @response_decorator
    def set_product_qty(
        self, barcode, current_source_location_id, dest_location_id, qty,
    ):
        (
            current_source_location,
            move_lines_children,
            product_move_lines,
            _,
            dest_location,
            product,
        ) = self._get_data_for_scan_products(
            current_source_location_id=current_source_location_id,
            dest_location_id=dest_location_id,
            product_barcode=barcode,
        )

        if not dest_location or not current_source_location:
            data = self._create_data_for_scan_products(
                move_lines_children, current_source_location.id, dest_location.id,
            )
            raise LocationNotFound(
                state="scan_products", data=data,
            )

        if len(product_move_lines) == 0:
            data = self._create_data_for_scan_products(
                move_lines_children, current_source_location.id, dest_location.id,
            )
            raise BarcodeNotFoundError(
                state="scan_products", data=data,
            )

        self._set_product_move_line_quantity(
            current_source_location,
            product_move_lines,
            qty,
            move_lines_children=move_lines_children,
            dest_location_id=dest_location.id,
            product=product,
        )

        return self._create_response_for_scan_products(
            move_lines_children,
            current_source_location.id,
            dest_location.id,
            product.barcode_ids,
        )

    @response_decorator
    def set_product_destination(
        self, barcode, product_barcode, current_source_location_id, dest_location_id,
    ):
        (
            current_source_location,
            move_lines_children,
            product_move_lines,
            barcode_location,
            dest_location,
            product,
        ) = self._get_data_for_scan_products(
            current_source_location_id=current_source_location_id,
            location_barcode=barcode,
            product_barcode=product_barcode,
            dest_location_id=dest_location_id,
        )

        if not barcode_location:
            data = self._create_data_for_scan_products(
                move_lines_children,
                current_source_location.id,
                dest_location.id,
                product.barcode_ids,
            )
            raise LocationNotFound(
                state="scan_products", data=data,
            )

        if (
            not barcode_location.is_sublocation_of(dest_location)
            and barcode_location.id != dest_location.id
            and barcode_location.id != current_source_location.id
        ):
            data = self._create_data_for_scan_products(
                move_lines_children,
                current_source_location.id,
                dest_location.id,
                product.barcode_ids,
            )
            raise DestLocationNotAllowed(
                state="scan_products", data=data,
            )

        message = None
        move_lines_done = None

        if barcode_location.id == current_source_location.id:
            self._reset_product_quantity(product_move_lines)
            message = {
                "message_type": "success",
                "body": "Product succesfully put back in source location",
            }
        else:
            message, move_lines_done = self._put_move_lines_in_destination(
                product_move_lines, barcode_location
            )

        (_, new_move_lines_children, _, _, _, _,) = self._get_data_for_scan_products(
            current_source_location_id,
        )

        return self._create_response_for_scan_products(
            new_move_lines_children,
            current_source_location.id,
            message=message,
            move_lines_done=move_lines_done,
            selected_location_id=dest_location.id,
        )


class ShopfloorStockBatchTransferValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.stock.batch.transfer.validator"
    _usage = "stock_batch_transfer.validator"

    def list_input_location(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def set_current_location(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "current_source_location_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }

    def drop_product_to_location(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "current_source_location_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "dest_location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_product_qty(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "current_source_location_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "dest_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_product_destination(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "product_barcode": {"required": True, "type": "string"},
            "current_source_location_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "dest_location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorStockBatchTransferValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.stock.batch.transfer.validator.response"
    _usage = "stock_batch_transfer.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_input_locations,
            "scan_products": self._schema_move_lines,
        }

    @property
    def _schema_input_locations(self):
        return {
            "input_locations": self.schemas._schema_list_of(
                self.schemas_detail.location_detail()
            ),
        }

    @property
    def _schema_move_lines(self):
        return {
            "move_lines": self.schemas._schema_list_of(
                self.schemas.move_line(with_packaging=True, with_picking=True)
            ),
            "id": {"required": True, "type": "integer"},
            "selected_location": {
                "required": False,
                "type": "integer",
                "nullable": True,
            },
            "selected_product": {
                "type": "list",
                "nullable": True,
                "schema": {"type": "string"},
                "required": False,
            },
            "move_lines_done": {
                "type": "list",
                "nullable": True,
                "schema": {"type": "integer"},
            },
        }

    def list_input_location(self):
        return self._response_schema(next_states={"start"},)

    def scan_location(self):
        return self._response_schema(next_states={"start", "scan_products"})

    def set_current_location(self):
        return self._response_schema(next_states={"scan_products"})

    def drop_product_to_location(self):
        return self._response_schema(next_states={"scan_products"})

    def set_product_qty(self):
        return self._response_schema(next_states={"scan_products"})

    def set_product_destination(self):
        return self._response_schema(next_states={"scan_products"})
