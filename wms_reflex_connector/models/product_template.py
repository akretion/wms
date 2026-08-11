# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    wms_error_sync_ids = fields.One2many(
        "wms.product.sync",
        compute="_compute_wms_error",
    )
    wms_error_sync = fields.Boolean(
        compute="_compute_wms_error",
    )

    def _compute_wms_error(self):
        for record in self:
            record.wms_error_sync_ids = (
                record.product_variant_ids.wms_sync_ids.filtered("wms_export_error")
            )
            record.wms_error_sync = bool(record.wms_error_sync_ids)

    def force_reflex_export(self):
        self.reflex_export = True
        self = self.sudo()
        # Force sync
        wms = self.env["stock.warehouse"].search([("active_wms_sync", "=", True)])
        wms.refresh_wms_products()
        # Force Export
        self.product_variant_ids.wms_sync_ids.with_context(
            force_reflex_export=True
        ).synchronize_export()
