# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from odoo import api, fields, models


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    def _read_reflex_data(self):
        return io.StringIO(base64.b64decode(self.datas).decode("latin-1"), newline=None)

    def _run_wms_picking_in(self):
        return (
            self.env["processor.picking.in"]
            .with_context(
                warehouse=self.warehouse_id,
                attachment_queue=self,
            )
            .run(self._read_reflex_data())
        )

    def _run_wms_picking_out(self):
        return (
            self.env["processor.picking.out"]
            .with_context(
                warehouse=self.warehouse_id,
                attachment_queue=self,
            )
            .run(self._read_reflex_data())
        )

    def _run_wms_stock_inventory(self):
        return (
            self.env["processor.inventory"]
            .with_context(
                warehouse=self.warehouse_id,
                attachment_queue=self,
            )
            .run(self.name, self._read_reflex_data())
        )

    def run_do_not_raise_error(self):
        return self.with_context(do_not_raise_error=True).run()
