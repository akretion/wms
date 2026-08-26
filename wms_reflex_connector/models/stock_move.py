# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    wms_export_date = fields.Datetime(related="picking_id.wms_export_date")

    def _do_unreserve(self):
        if not self._context.get("validation_from_sync"):
            for record in self:
                if (
                    record.picking_id.picking_type_id.code == "outgoing"
                    and record.picking_id.wms_export_date
                ):
                    raise UserError(
                        _(
                            "La réservation du mouvement %(move_name)s du picking "
                            "%(picking_name)s ne peut pas être annulée car le "
                            "bon à été envoyé au WMS"
                        )
                        % dict(
                            move_name=record.name, picking_name=record.picking_id.name
                        )
                    )
        return super()._do_unreserve()
