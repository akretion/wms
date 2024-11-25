# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _inherit = "shopfloor.search.action"

    def mrp_production_from_scan(self, barcode, limit=1):
        model = self.env["mrp.production"]
        if not barcode:
            return model.browse()
        return model.search([("name", "=", barcode)], limit=1)
