# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    LocationNotFound,
    InventoryNotFound,
    ProductNotInInventory,
    response_decorator,
)


class Inventory(Component):
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
    _name = "shopfloor.inventory"
    _usage = "inventory"
    _description = __doc__

    def _get_data_for_scan_products(
        self,
        inventory_id,
        location_barcode=None,
        location_id_prout_prout=None,
        product_barcode=None,
        product_id=None,
        product_scanned_list_id=[],
    ):
        search = self._actions_for("search")
        location = None
        product = None
        product_scanned_list = None
        new_product = None

        if location_barcode:
            location = search.location_from_scan(location_barcode)

        if location_id_prout_prout:
            location = self.env["stock.location"].browse(location_id_prout_prout)

        product_lines = self.env["stock.inventory.line"].search([
            ("inventory_id.id", "=", inventory_id),
            ("location_id.id", "=", location_id_prout_prout),
        ])

        if product_barcode:
            product = next((p for p in product_lines if (product_barcode in [barcode.name for barcode in p.product_id.mapped("barcode_ids")])), None)
            if product:
                product_scanned_list_id.append(product.id)

        if product_id:
            product = next((p for p in product_lines if p.product_id.id == product_id), None)

        if product_barcode and not product:
            new_product = search.product_from_scan(product_barcode)

        product_scanned_list_search = list(set(product_scanned_list_id))
        product_scanned_list = self.env["stock.inventory.line"].search([
            ("inventory_id.id", "=", inventory_id),
            ("location_id.id", "=", location_id_prout_prout),
            ("id", "in", product_scanned_list_search),
        ])

        return (
            self.env["stock.inventory.line"].search(
                [("inventory_id", "=", inventory_id)],
            ),
            location,
            product,
            [p.id for p in product_scanned_list],
            new_product,
        )

    def _create_data_for_scan_products(
        self,
        inventory_id,
        inventory_lines,
        selected_location_id=None,
        product_scanned_list=[]
    ):
        return {
            "inventory_id": inventory_id,
            "inventory_lines": self.data_detail.inventory_lines(inventory_lines),
            "selected_location": selected_location_id,
            "product_scanned_list": product_scanned_list,
        }


    def _create_response_for_scan_products(
        self,
        inventory_id,
        inventory_lines,
        selected_location_id=None,
        product_scanned_list=[],
        message=None,
    ):
        data = self._create_data_for_scan_products(
            inventory_id,
            inventory_lines,
            selected_location_id,
            product_scanned_list,
        )

        return self._response(
            next_state="scan_product", data=data, message=message,
        )

    def _create_data_for_start(
        self,
    ):
        inventories = self.env["stock.inventory"].search(
            [("state", "=", "confirm")],
            order="date asc",
        )

        inventories_data = self.data.inventories(inventories)

        return {"inventories": inventories_data}


    @response_decorator
    def list_inventory(self):
        data = self._create_data_for_start()

        return self._response(
            next_state="start", data=data
        )

    @response_decorator
    def select_inventory(self, inventory_id):
        inventory_lines, _, _, _, _ = self._get_data_for_scan_products(inventory_id)

        if len(inventory_lines) == 0:
            data = self._create_data_for_start()
            raise InventoryNotFound(
                state="start", data=data
            )

        return self._create_response_for_scan_products(
            inventory_id,
            inventory_lines,
        )

    @response_decorator
    def select_location(self, inventory_id, location_barcode):
        inventory_lines, location, _, _, _ = self._get_data_for_scan_products(inventory_id, location_barcode)

        if not location:
            data = self._create_data_for_scan_products(
                inventory_id,
                inventory_lines,
            )
            raise LocationNotFound(state="scan_product", data=data)

        return self._create_response_for_scan_products(
            inventory_id,
            inventory_lines,
            location.id,
            message={
                "message_type": "success",
                "body": "Selected location {}".format(location.name),
            }
        )

    @response_decorator
    def scan_product(self, inventory_id, location_id, barcode, product_scanned_list_id):
        inventory_lines, location, product, product_scanned_list, new_product = self._get_data_for_scan_products(
            inventory_id,
            location_id_prout_prout=location_id,
            product_barcode=barcode,
            product_scanned_list_id=product_scanned_list_id,
        )

        if not location:
            data = self._create_data_for_scan_products(
                inventory_id,
                inventory_lines,
                None,
                product_scanned_list,
            )
            raise LocationNotFound(state="scan_product", data=data)

        if not product and not new_product:
            data = self._create_data_for_scan_products(
                inventory_id,
                inventory_lines,
                location.id,
                product_scanned_list,
            )
            raise ProductNotInInventory(state="scan_product", data=data)

        if product:
            product.product_qty += 1

        if new_product:
            inventory = self._actions_for("inventory")
            line = inventory.create_inventory_line(
                inventory_id,
                location.id,
                new_product.id,
                1
            )
            inventory_lines = self.env["stock.inventory.line"].search(
                [("inventory_id", "=", inventory_id)],
            )
            product_scanned_list.append(line.id)

        return self._create_response_for_scan_products(
            inventory_id,
            inventory_lines,
            location.id,
            product_scanned_list,
        )

    @response_decorator
    def set_quantity(self, inventory_id, location_id, product_id, product_scanned_list_id, qty):
        inventory_lines, location, inventory_line, product_scanned_list, _ = self._get_data_for_scan_products(
            inventory_id,
            location_id_prout_prout=location_id,
            product_id=product_id,
            product_scanned_list_id=product_scanned_list_id,
        )

        if not location:
            data = self._create_data_for_scan_products(
                inventory_id,
                inventory_lines,
            )
            raise LocationNotFound(state="scan_product", data=data)

        if not inventory_line:
            data = self._create_data_for_scan_products(
                inventory_id,
                inventory_lines,
                location.id,
            )
            raise ProductNotInInventory(state="scan_product", data=data)

        if inventory_line:
            inventory_line.product_qty = qty

        if qty == 0 and inventory_line.created_from_shopfloor:
            inventory_line.sudo().unlink()
            inventory_lines = self.env["stock.inventory.line"].search(
                [("inventory_id", "=", inventory_id)],
            )
            product_scanned_list.remove(inventory_line.id)

        return self._create_response_for_scan_products(
            inventory_id,
            inventory_lines,
            location.id,
            product_scanned_list,
        )

class ShopfloorStockBatchTransferValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.inventory.validator"
    _usage = "inventory.validator"

    def list_inventory(self):
        return {}

    def select_inventory(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def select_location(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_barcode": {"required": True, "type": "string"},
        }

    def scan_product(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "product_scanned_list_id": {"required": True, "type": "list", "schema":{"type": "integer"}},
        }

    def set_quantity(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_scanned_list_id": {"required": True, "type": "list", "schema":{"type": "integer"}},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

class ShopfloorStockBatchTransferValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.inventory.validator.response"
    _usage = "inventory.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_inventory,
            "scan_product": self._schema_line_inventory,
        }

    @property
    def _schema_inventory(self):
        return {
            "inventories": self.schemas._schema_list_of(
                self.schemas.inventory()
            ),
        }

    @property
    def _schema_line_inventory(self):
        return {
            "inventory_lines": self.schemas._schema_list_of(
                self.schemas_detail.inventory_line()
            ),
            "inventory_id": {"type": "integer", "required": True},
            "selected_location": {"type": "integer", "required": False, "nullable": True},
            "product_scanned_list": {"type": "list", "schema": {"type": "integer", "required": True}, "required": True},
        }

    def list_inventory(self):
        return self._response_schema(next_states={"start"},)

    def select_inventory(self):
        return self._response_schema(next_states={"scan_product"},)

    def select_location(self):
        return self._response_schema(next_states={"scan_product"},)

    def scan_product(self):
        return self._response_schema(next_states={"scan_product"},)

    def set_quantity(self):
        return self._response_schema(next_states={"scan_product"},)
