# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.addons.attachment_synchronize_record.tests.common import (
    SynchronizeRecordCommon,
)


class WmsConnectorCommon(SynchronizeRecordCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")

    def setAllExported(self):
        self.env["stock.picking"].search([]).export_date = datetime.date.today()
        self.env["wms.product.sync"].search([]).export_date = datetime.date.today()
