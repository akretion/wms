# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "WMS reflex connector",
    "summary": """
        WMS reflex connector that offers an API to parse and construct the reflex file format. Also provides basics FTP drop and pickup for Reflex FTP server.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion",
    "depends": [
        "wms_connector",
        "storage_backend_ftp",
    ],
    "external_dependencies": {"python": ["unidecode"]},
    "data": [],
    "demo": [],
}
