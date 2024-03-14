# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class SynchronizeExportableMixin(models.AbstractModel):
    _inherit = "synchronize.exportable.mixin"

    def _synchronize_context_hook(self, warehouse):
        return {"warehouse": warehouse}
