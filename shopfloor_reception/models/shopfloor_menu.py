from odoo import api, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    reception_without_pack = fields.Boolean(
        string="Do no process with pack",
        default=False,
    )
    reception_without_pack_is_possible = fields.Boolean(
        compute="_compute_reception_without_pack_is_possible"
    )

    @api.depends("scenario_id")
    def _compute_reception_without_pack_is_possible(self):
        for menu in self:
            menu.reception_without_pack_is_possible = menu.scenario_id.has_option(
                "reception_without_pack"
            )
