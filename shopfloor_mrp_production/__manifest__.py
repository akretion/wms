# Copyright 2024 Akretion (https://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor MRP Production",
    "summary": "MRP with shopfloor",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["hparfr"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "shopfloor",
        "mrp",
    ],
    "data": [
        "data/shopfloor_mrp_scenario.xml",
    ],
    "demo": [
        "demo/shopfloor_mrp_production_demo.xml",
    ],
    "installable": True,
}
