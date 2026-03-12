# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from openupgradelib import openupgrade


def move_fields_to_new_module(cr):
    # is_shopfloor_created has been wrongly put in shopfloor_reception.
    # this script moves it in shopfloor.

    # avoid crash if shopfloor is updated before shopfloor_reception
    cr.execute(
        """
        SELECT id FROM ir_model_data
        WHERE module = 'shopfloor'
        AND model = 'ir.model.fields'
        AND name = 'field_stock_picking__is_shopfloor_created'
        """
    )
    if not cr.fetchone():
        openupgrade.update_module_moved_fields(
            cr,
            "stock.picking",
            ["is_shopfloor_created"],
            "shopfloor_reception",
            "shopfloor",
        )


def migrate(cr, version):
    move_fields_to_new_module(cr)
