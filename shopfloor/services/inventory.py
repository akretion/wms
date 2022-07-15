# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.exceptions import ShopfloorError

from .exception import LocationNotFound, ProductNotInInventory


class Inventory(Component):
    """ """

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
        product_scanned_list_id=None,
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

        product_lines = self.env["stock.inventory.line"].search(
            [
                ("inventory_id.id", "=", inventory_id),
                ("location_id.id", "=", location_id_prout_prout),
            ]
        )

        if product_barcode:
            product = next(
                (
                    p
                    for p in product_lines
                    if (
                        product_barcode
                        in [
                            barcode.name
                            for barcode in p.product_id.mapped("barcode_ids")
                        ]
                    )
                ),
                None,
            )
            if product:
                product_scanned_list_id.append(product.id)

        if product_id:
            product = next(
                (p for p in product_lines if p.product_id.id == product_id), None
            )

        if product_barcode and not product:
            new_product = search.product_from_scan(product_barcode)

        product_scanned_list_search = list(set(product_scanned_list_id))
        product_scanned_list = self.env["stock.inventory.line"].search(
            [
                ("inventory_id.id", "=", inventory_id),
                ("location_id.id", "=", location_id_prout_prout),
                ("id", "in", product_scanned_list_search),
            ]
        )

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
        product_scanned_list=None,
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
        product_scanned_list=None,
        message=None,
    ):
        data = self._create_data_for_scan_products(
            inventory_id,
            inventory_lines,
            selected_location_id,
            product_scanned_list,
        )

        return self._response(
            next_state="scan_product",
            data=data,
            message=message,
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

    def _response_for_start(self, message=None, popup=None):
        return self._response(next_state="start", message=message, popup=popup)

    def _response_for_confirm_start(self, inventory):
        return self._response(
            next_state="confirm_start",
            data=self.data.inventory(inventory),
        )

    def _response_for_manual_selection(self, inventories, message=None):
        data = {
            "records": self.data.inventories(inventories),
            "size": len(inventories),
        }
        return self._response(next_state="manual_selection", data=data, message=message)

    def _response_for_start_location(self, inventory, message=None, popup=None):
        return self._response(
            next_state="start_location",
            data=self._data_inventory_location(inventory),
            message=message,
            popup=popup,
        )

    def _response_for_scan_product(self, inventory, location, message=None):
        data = self._data_inventory_location(inventory, location)
        return self._response(next_state="scan_product", data=data, message=message)

    def _response_for_empty_location(
        self, inventory, location, message=None, popup=None
    ):
        return self._response(
            next_state="empty_location",
            data=self._data_inventory_location(inventory, location),
            message=message,
            popup=popup,
        )

    def _response_inventory_does_not_exist(self):
        return self._response_for_start(message=self.msg_store.record_not_found())

    def find_inventory(self):
        inventories = self._inventory_search()
        selected = self._select_an_inventory(inventories)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response_for_start(
                message={
                    "message_type": "info",
                    "body": _("No more work to do, please create a new inventory"),
                },
            )

    def list_inventory(self):
        inventories = self._inventory_search()
        return self._response_for_manual_selection(inventories)

    def select_inventory(self, inventory_id):
        inventories = self._inventory_search(inventory_ids=[inventory_id])
        selected = self._select_an_inventory(inventories)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response(
                base_response=self.list_inventory(),
                message={
                    "message_type": "warning",
                    "body": _("This inventory cannot be selected."),
                },
            )

    def _inventory_base_search_domain(self):
        return [
            "|",
            ("user_id", "=", False),
            ("user_id", "=", self.env.user.id),
            ("state", "=", "confirm"),
        ]

    def _inventory_search(self, name_fragment=None, inventory_ids=None):
        domain = self._inventory_base_search_domain()
        if name_fragment:
            domain = expression.AND([domain, [("name", "ilike", name_fragment)]])
        if inventory_ids:
            domain = expression.AND([domain, [("id", "in", inventory_ids)]])
        records = self.env["stock.inventory"].search(domain, order="id asc")
        #        records = records.filtered(self._inventory_filter)
        return records

    def _select_an_inventory(self, inventories):
        # first look for started inventory assigned to self
        candidates = inventories.filtered(
            lambda inv: inv.user_id == self.env.user
            and any(loc.state != "pending" for loc in inv.sub_location_ids)
        )
        if candidates:
            return candidates[0]
        # then look for confirm assigned to self
        candidates = inventories.filtered(lambda inv: inv.user_id == self.env.user)
        if candidates:
            return candidates[0]
        # finally take any inventory that search could return
        if inventories:
            inventory = inventories[0]
            inventory.write({"user_id": self.env.uid})
            return inventory
        return self.env["stock.inventory"]

    def confirm_start(self, inventory_id):
        """User confirms they start a batch

        Should have no effect in odoo besides logging and routing the user to
        the next action. The next action is "start_line" with data about the
        line to pick.

        Transitions:
        * start_line: when the batch has at least one line without destination
          package
        * start: if the condition above is wrong (rare case of race condition...)
        """
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        inventory.user_id = self.env.user.id
        if len(inventory.location_ids) == 1 and not inventory.location_ids.child_ids:
            return self._response_for_scan_product(inventory, inventory.location_ids)
        return self._response_for_start_location(inventory)

    def start_location(self, inventory_id, barcode):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if not location:
            return self._response_for_start_location(
                inventory, message=self.msg_store.no_location_found()
            )
        location_state = inventory.sub_location_ids.filtered(
            lambda l: l.location_id == location
        )
        if location_state == "done":
            # TODO re-inventory or update location instead of raise
            raise ShopfloorError(
                self.msg_store.location_already_inventoried(barcode),
                next_state="start_location",
            )
        if location.has_ongoing_operation():
            raise ShopfloorError(
                self.msg_store.has_on_going_operation(location),
                next_state="start_location",
            )
        location_state.action_start()
        return self._response_for_scan_product(inventory, location)

    def scan_product(self, inventory_id, location_id, barcode, quantity=0):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        if product:
            if product.tracking in ["lot", "serial"]:
                return self._response_for_scan_product(
                    inventory,
                    location,
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            if quantity:
                self._set_quantity(inventory, location, product, quantity)
            else:
                self._increase_quantity(inventory, location, product)
            return self._response_for_scan_product()
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            if packaging.product_id.tracking in ["lot", "serial"]:
                return self._response_for_scan_product(
                    inventory,
                    location,
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            product = packaging.product_id
            if quantity:
                self._set_quantity(inventory, location, product, quantity)
            else:
                self._increase_quantity(inventory, location, product)
            return self._response_for_scan_product()
        lot = search.lot_from_scan(barcode)
        if lot:
            product = lot.product_id
            if quantity:
                self._set_quantity(inventory, location, product, quantity, lot=lot)
            else:
                self._increase_quantity(inventory, location, product, lot=lot)
            return self._response_for_scan_product()
        other_location = search.location_from_scan(barcode)
        if other_location and other_location != location:
            return self._location_counted(inventory, location, other_location)
        return self._response_for_scan_product(
            inventory, location, message=self.msg.store.no_product_for_barcode(barcode)
        )

    def select_location(self, inventory_id, location_barcode):
        inventory_lines, location, _, _, _ = self._get_data_for_scan_products(
            inventory_id, location_barcode
        )

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
            },
        )

    def old_scan_product(
        self, inventory_id, location_id, barcode, product_scanned_list_id
    ):
        (
            inventory_lines,
            location,
            product,
            product_scanned_list,
            new_product,
        ) = self._get_data_for_scan_products(
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
                inventory_id, location.id, new_product.id, 1
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

    def set_quantity(
        self, inventory_id, location_id, product_id, product_scanned_list_id, qty
    ):
        (
            inventory_lines,
            location,
            inventory_line,
            product_scanned_list,
            _,
        ) = self._get_data_for_scan_products(
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

    def location_empty(self, inventory_id, location_id):
        return


class ShopfloorInventoryValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.inventory.validator"
    _usage = "inventory.validator"

    def find_inventory(self):
        return {}

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
            "product_scanned_list_id": {
                "required": True,
                "type": "list",
                "schema": {"type": "integer"},
            },
        }

    def set_quantity(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_scanned_list_id": {
                "required": True,
                "type": "list",
                "schema": {"type": "integer"},
            },
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
            "inventories": self.schemas._schema_list_of(self.schemas.inventory()),
        }

    @property
    def _schema_line_inventory(self):
        return {
            "inventory_lines": self.schemas._schema_list_of(
                self.schemas_detail.inventory_line()
            ),
            "inventory_id": {"type": "integer", "required": True},
            "selected_location": {
                "type": "integer",
                "required": False,
                "nullable": True,
            },
            "product_scanned_list": {
                "type": "list",
                "schema": {"type": "integer", "required": True},
                "required": True,
            },
        }

    def list_inventory(self):
        return self._response_schema(
            next_states={"start"},
        )

    def select_inventory(self):
        return self._response_schema(
            next_states={"scan_product"},
        )

    def select_location(self):
        return self._response_schema(
            next_states={"scan_product"},
        )

    def scan_product(self):
        return self._response_schema(
            next_states={"scan_product"},
        )

    def set_quantity(self):
        return self._response_schema(
            next_states={"scan_product"},
        )
