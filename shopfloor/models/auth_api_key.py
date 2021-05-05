# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class AuthApiKey(models.Model):
    _inherit = "auth.api.key"

    def _selection_scope(self):
        selection = super()._selection_scope()
        selection.append(("shopfloor", "Shopfloor"))
        return selection
