# Copyright 2020 Akretion (http://akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component

class Reception(Component):
    """
    Methods for the Reception Process
    """
    _inherit = "base.shopfloor.process"
    _name = "shopfloor.reception"
    _usage = "reception"
    _description = __doc__
