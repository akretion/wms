# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
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
    ):
        pass

    def _create_data_for_scan_products(
        self,
    ):
        pass

    def _create_response_for_scan_products(
        self,
    ):
        pass

    @response_decorator
    def list_inventory(self):
        inventories = self.env["stock.inventory"].search(
            [("state", "=", "confirm")],
            order="date asc",
        )

        inventories_data = self.data.inventories(inventories)

        return self._response(
            next_state="start", data={"inventories": inventories_data},
        );

    @response_decorator
    def scan_product(self):
        pass

class ShopfloorStockBatchTransferValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.inventory.validator"
    _usage = "inventory.validator"

    def list_inventory(self):
        return {}

    def scan_product(self):
        return {
            "barcode": {"required": True, "type": "string"},
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
        }

    @property
    def _schema_inventory(self):
        return {
            "inventories": self.schemas._schema_list_of(
                self.schemas_detail.inventory()
            ),
        }

    def list_inventory(self):
        return self._response_schema(next_states={"start"},)

