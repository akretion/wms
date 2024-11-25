# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class MrpProduction(Component):
    """Methods for the MRP Production

    You will find a sequence diagram describing states and endpoints
    relationships [here](../docs/single_pack_transfer_diag_seq.png).
    Keep [the sequence diagram](../docs/single_pack_transfer_diag_seq.plantuml)
    up-to-date if you change endpoints.
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.mrp.production"
    _usage = "mrp_production"
    _description = __doc__

    def _data_after_mrp_production(self, mrp_production):
        return {
            "id": mrp_production.id,
            "name": mrp_production.name,
            "location_src": self.data.location(mrp_production.location_src_id),
            "location_dest": self.data.location(mrp_production.location_dest_id),
            "product": self.data.product(mrp_production.product_id),
            "qty_to_produce": mrp_production.product_qty - mrp_production.qty_produced,
        }

    def _response_for_start(self, message=None, popup=None):
        return self._response(next_state="start", message=message, popup=popup)

    def _response_for_scan_location(
        self, mrp_production, message=None, confirmation_required=None
    ):
        data = self._data_after_mrp_production(mrp_production)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="scan_location",
            data=data,
            message=message,
        )

    def _response_for_confirm_start(self, package_level, message=None, barcode=""):
        data = self._data_after_package_scanned(package_level)
        data["confirmation_required"] = barcode
        return self._response(
            next_state="start",
            data=data,
            message=message,
        )

    def _response_for_scan_mrp_production(
        self, mrp_production, message=None, confirmation_required=None
    ):
        data = self._data_after_mrp_production(mrp_production)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="scan_location",
            data=data,
            message=message,
        )

    def _scan_source(self, barcode, confirmation=None):
        """Search a mrp.prod / product / package ?"""
        search = self._actions_for("search")

        mrp_prod = search.mrp_production_from_scan(barcode)

        if not mrp_prod:
            return (self.msg_store.mrp_prod_not_found_for_barcode(barcode), None)
        elif mrp_prod.state == "done":
            return (self.msg_store.mrp_prod_alredy_done(mrp_prod), None)
        elif mrp_prod.state == "draft":
            return (self.msg_store.mrp_prod_still_in_draft(mrp_prod), None)
        elif mrp_prod.state == "cancel":
            return (self.msg_store.mrp_prod_canceled(mrp_prod), None)
        elif not mrp_prod.state == "confirmed":
            return (self.msg_store.mrp_prod_unknown_state(mrp_prod), None)
        return (None, mrp_prod)

    def start(self, barcode, confirmation=None):
        message, mo = self._scan_source(barcode, confirmation)
        if message:
            return self._response_for_start(message=message)
        return self._response_for_scan_mrp_production(mo)

    def cancel(self):
        # cancel is go back to start state
        return self._response_for_start()

    def validate(self, mrp_production_id, location_barcode, confirmation=None):
        """Validate the transfer"""
        search = self._actions_for("search")

        mrp_production = self.env["mrp.production"].browse(mrp_production_id)
        if not mrp_production.exists():
            return self._response_for_start(
                message=self.msg_store.operation_not_found()
            )

        scanned_location = search.location_from_scan(location_barcode)
        if not scanned_location:
            return self._response_for_scan_location(
                mrp_production, message=self.msg_store.no_location_found()
            )

        # copy pasted from is_dest_location_valid but adapted to mrp
        # because mrp_production.location_dest_id has no picking_id
        if not (
            scanned_location.is_sublocation_of(
                mrp_production.location_dest_id, func=all
            )
            or scanned_location.is_sublocation_of(
                mrp_production.picking_type_id.default_location_dest_id, func=all
            )
        ):
            return self._response_for_scan_location(
                mrp_production, message=self.msg_store.dest_location_not_allowed()
            )

        if confirmation != location_barcode and self.is_dest_location_to_confirm(
            mrp_production.location_dest_id, scanned_location
        ):
            return self._response_for_scan_location(
                mrp_production,
                confirmation_required=location_barcode,
                message=self.msg_store.confirm_location_changed(
                    mrp_production.location_dest_id, scanned_location
                ),
            )

        self._set_destination_and_done(mrp_production, scanned_location)
        return self._router_validate_success(mrp_production)

    def _set_destination_and_done(self, mrp_production, scanned_location):
        mrp_production.move_finished_ids.location_dest_id = scanned_location
        mrp_production.qty_producing = (
            mrp_production.product_qty - mrp_production.qty_produced
        )
        mrp_production._set_qty_producing()
        # we don't handle input of lot numbers yet, so it should generate an error
        mrp_production.button_mark_done()
        # with_context({"skip_immediate": True}).

    def _router_validate_success(self, mrp_production):
        message = self.msg_store.confirm_mrp_production_done(mrp_production)
        completion_info_popup = None
        return self._response_for_start(message=message, popup=completion_info_popup)


class MrpProductionValidator(Component):
    """Validators for MRP Production"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.mrp.production.validator"
    _usage = "mrp_production.validator"

    def start(self):
        return {
            "barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "string", "required": False},
        }

    def cancel(self):
        return {}

    def validate(self):
        return {
            "mrp_production_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "location_barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "string", "required": False},
        }


class MRPProductionValidatorResponse(Component):
    """Validators for MRP Production responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.mrp.production.validator.response"
    _usage = "mrp_production.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        schema_for_start = self._schema_for_mrp_production()
        schema_for_start.update(self._schema_confirmation_required())
        schema_for_scan_location = self._schema_for_mrp_production(required=True)
        schema_for_scan_location.update(self._schema_confirmation_required())
        return {
            "start": schema_for_start,
            "scan_location": schema_for_scan_location,
        }

    def start(self):
        return self._response_schema(next_states={"start", "scan_location"})

    def cancel(self):
        return self._response_schema(next_states={"start"})

    def validate(self):
        return self._response_schema(next_states={"scan_location", "start"})

    def _schema_for_mrp_production(self, required=False):
        # TODO use schemas.package_level (but the "name" moves in "package.name")
        return {
            "id": {"required": required, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": required},
            "location_src": {"type": "dict", "schema": self.schemas.location()},
            "location_dest": {"type": "dict", "schema": self.schemas.location()},
            "product": {"type": "dict", "schema": self.schemas.product()},
            "qty_to_produce": {"type": "float"},
        }

    def _schema_confirmation_required(self):
        return {
            "confirmation_required": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
        }
