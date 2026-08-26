# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import groupby


class StockPicking(models.Model):
    _inherit = ["reflex.exportable.mixin", "stock.picking"]
    _name = "stock.picking"

    @property
    def file_creation_mode(self):
        return "per_record"

    def _get_export_name(self):
        raise NotImplementedError()

    def _is_user_allowed_to_validate(self):
        return True

    def button_validate(self):
        for record in self:
            if (
                record.is_wms_exportable
                and not record._context.get("validation_from_sync")
                and not self._is_user_allowed_to_validate()
            ):
                raise UserError("Vous n'avez pas les droits de valider ce transfert")
        return super().button_validate()
