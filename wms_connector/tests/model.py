# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class WmsProductSync(models.Model):
    _inherit = ["wms.product.sync"]

    def _prepare_export_data(self, _):
        res = []
        for rec in self:
            res += [
                {"name": rec.product_id.name, "reference": rec.product_id.default_code}
            ]
            if len(rec.product_id.name) > 100:
                raise ValueError("Boom")
        return res

    def _get_export_name(self):
        return self.name

    def _get_export_task(self):
        return self.warehouse_id.wms_export_task_id


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_export_data(self, _):
        return [
            {
                "name": rec.name,
            }
            for rec in self
        ]

    def _get_export_name(self):
        return self.name

    def _get_export_task(self):
        return self.location_id.warehouse_id.wms_export_task_id
