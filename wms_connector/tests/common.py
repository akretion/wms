# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo_test_helper import FakeModelLoader

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
        self.env["wms.product.sync"].search([]).to_export = False


class WmsConnectorCase(WmsConnectorCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref(
            "attachment_synchronize.export_to_filestore"
        ).backend_id = cls.backend
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .model import StockPicking, WmsProductSync

        cls.loader.update_registry((WmsProductSync, StockPicking))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()
