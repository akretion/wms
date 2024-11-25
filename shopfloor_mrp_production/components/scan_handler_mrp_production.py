# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class MrpProductionHandler(Component):
    """Scan anything handler for stock.picking."""

    _name = "shopfloor.scan.mpr_production.handler"
    _inherit = "shopfloor.scan.anything.handler"

    record_type = "mpr_production"

    def search(self, identifier):
        res = self._search.find(identifier, types=("mpr_production",))
        return res.record if res.record else self.env["mrp.production"]

    @property
    def converter(self):
        return self._data_detail.picking_detail

    def schema(self):
        return self._schema_detail.picking_detail()
