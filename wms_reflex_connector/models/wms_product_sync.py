import inspect
from dataclasses import dataclass
from enum import Enum
from typing import Any

from odoo import fields, models
from odoo.exceptions import ValidationError


class WmsProductSync(models.Model):
    _inherit = ["reflex.exportable.mixin", "wms.product.sync"]
    _name = "wms.product.sync"

    def _should_export_product(self):
        return True

    def _get_export_name(self):
        raise NotImplementedError()

    @property
    def record_per_file(self):
        return 1000

    def _format_to_exportfile_txt(self, data):
        vals = super()._format_to_exportfile_txt(data)
        vals["task_id"] = self.warehouse_id.wms_export_task_id.id
        return vals

    def track_export(self, attachment):
        super().track_export(attachment)
        if self._context.get("force_reflex_export"):
            attachment._run()
            vals = {
                "state": "done",
                "date_done": fields.Datetime.now(),
            }
            attachment.write(vals)
