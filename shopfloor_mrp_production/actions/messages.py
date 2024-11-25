# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def mrp_prod_not_found_for_barcode(self, barcode):
        return {
            "message_type": "error",
            "body": _("MO %(name)s not found") % dict(name=barcode),
        }

    def mrp_prod_alredy_done(self, mpr_production):
        return {
            "message_type": "error",
            "body": _("MO %(name)s already done") % dict(name=mpr_production.name),
        }

    def mrp_prod_still_in_draft(self, mpr_production):
        return {
            "message_type": "error",
            "body": _("MO %(name)s is still in draft. It should be confirmed on odoo")
            % dict(name=mpr_production.name),
        }

    def mrp_prod_canceled(self, mpr_production):
        return {
            "message_type": "error",
            "body": _("MO %(name)s has been canceled") % dict(name=mpr_production.name),
        }

    def mrp_prod_unknown_state(self, mpr_production):
        return {
            "message_type": "error",
            "body": _("MO %(name)s in unkown state") % dict(name=mpr_production.name),
        }

    def confirm_mrp_production_done(self, mpr_production):
        return {
            "message_type": "info",
            "body": _("MO %(name)s marked as done") % dict(name=mpr_production.name),
        }
