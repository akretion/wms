# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor MRP Production Mobile",
    "summary": "MRP with shopfloor mobile app",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["hparfr"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "shopfloor_mrp_production",
        "shopfloor_mobile",
    ],
    "data": [
        "templates/assets.xml",
    ],
    "installable": True,
}
