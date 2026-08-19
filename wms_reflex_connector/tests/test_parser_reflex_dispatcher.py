# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import inspect

from odoo.tests.common import TransactionCase

import odoo.addons.wms_reflex_connector.parser_reflex.dispatcher as dispatcher
from odoo.addons.wms_reflex_connector.parser_reflex.dispatcher import (
    ReflexDispatchError,
    ReflexInterfaceDispatcher,
)
from odoo.addons.wms_reflex_connector.parser_reflex.gei62 import (
    parse_record as parse_62,
)
from odoo.addons.wms_reflex_connector.parser_reflex.prep52 import (
    parse_record as parse_52,
)
from odoo.addons.wms_reflex_connector.parser_reflex.rec53 import (
    parse_record as parse_53,
)
from odoo.addons.wms_reflex_connector.parser_reflex.stock55 import (
    Reflex55ParseError,
)
from odoo.addons.wms_reflex_connector.parser_reflex.stock55 import (
    parse_record as parse_55,
)


class TestReflexInterfaceDispatcher(TransactionCase):
    """Contract tests for selecting existing pure Reflex interface parsers."""

    DIRECT_PARSERS = {
        "52": parse_52,
        "53": parse_53,
        "55": parse_55,
        "62": parse_62,
    }
    RUBRIQUES = {"52": "160", "53": "110", "55": "110", "62": "110"}

    def _record(self, interface, *, rubrique=None):
        payload = [" "] * 270

        def put(offset, value):
            payload[offset - 1 : offset - 1 + len(value)] = value

        put(1, "0000123")
        put(8, "HL")
        put(10, interface)
        put(12, rubrique or self.RUBRIQUES.get(interface, "110"))
        return "".join(payload)

    def _replace(self, record, offset, value):
        return record[: offset - 1] + value + record[offset - 1 + len(value) :]

    def _assert_dispatch_error(self, callback, expected):
        with self.assertRaises(ReflexDispatchError) as caught:
            callback()
        error = caught.exception
        self.assertEqual(
            (error.rubrique, error.field, error.offset, error.value), expected
        )

    def test_dispatches_every_registered_interface_to_its_direct_parser(self):
        parser = ReflexInterfaceDispatcher(("52", "53", "55", "62"))
        for interface, direct_parser in self.DIRECT_PARSERS.items():
            with self.subTest(interface=interface):
                record = self._record(interface)
                direct = direct_parser(record)
                dispatched = parser.parse(record)
                self.assertEqual(dispatched, direct)
                self.assertIsInstance(dispatched, type(direct))

    def test_allowlist_accepts_one_or_many_interfaces_and_empty_rejects_all(self):
        record_52 = self._record("52")
        record_53 = self._record("53")
        self.assertEqual(
            ReflexInterfaceDispatcher(("52",)).parse(record_52), parse_52(record_52)
        )
        parser = ReflexInterfaceDispatcher(("52", "53"))
        self.assertEqual(parser.parse(record_52), parse_52(record_52))
        self.assertEqual(parser.parse(record_53), parse_53(record_53))
        self._assert_dispatch_error(
            lambda: ReflexInterfaceDispatcher(()).parse(record_52),
            (None, "interface", 10, "52"),
        )

    def test_rejects_disallowed_and_unknown_interface_codes_before_delegation(self):
        parser = ReflexInterfaceDispatcher(("52",))
        self._assert_dispatch_error(
            lambda: parser.parse(self._record("53")),
            (None, "interface", 10, "53"),
        )
        self._assert_dispatch_error(
            lambda: parser.parse(self._record("99")),
            (None, "interface", 10, "99"),
        )

    def test_rejects_invalid_allowlist_entries_when_configured(self):
        for code in ("99", 52, None):
            with self.subTest(code=code):
                self._assert_dispatch_error(
                    lambda code=code: ReflexInterfaceDispatcher((code,)),
                    (None, "allowed_interfaces", 0, repr(code)),
                )

    def test_rejects_non_text_short_and_malformed_common_envelopes(self):
        parser = ReflexInterfaceDispatcher(("52",))
        self._assert_dispatch_error(
            lambda: parser.parse(None),
            (None, "record", 1, "None"),
        )
        self._assert_dispatch_error(
            lambda: parser.parse("0000123HL5"),
            (None, "record", 1, "0000123HL5"),
        )
        self._assert_dispatch_error(
            lambda: parser.parse(self._replace(self._record("52"), 8, "XX")),
            (None, "application", 8, "XX"),
        )
        embedded_newline = self._record("52")[:20] + "\n" + self._record("52")[20:]
        self._assert_dispatch_error(
            lambda: parser.parse(embedded_newline),
            (None, "record", 1, embedded_newline),
        )

    def test_accepts_one_lf_or_crlf_terminator_for_dispatch(self):
        record = self._record("53")
        parser = ReflexInterfaceDispatcher(("53",))
        self.assertEqual(parser.parse(record + "\n"), parse_53(record))
        self.assertEqual(parser.parse(record + "\r\n"), parse_53(record))

    def test_preserves_the_selected_parser_error_unchanged(self):
        record = self._replace(self._record("55"), 140, "0000X0001")
        with self.assertRaises(Reflex55ParseError) as direct_caught:
            parse_55(record)
        with self.assertRaises(Reflex55ParseError) as dispatched_caught:
            ReflexInterfaceDispatcher(("55",)).parse(record)
        self.assertEqual(
            (
                dispatched_caught.exception.rubrique,
                dispatched_caught.exception.field,
                dispatched_caught.exception.offset,
                dispatched_caught.exception.value,
            ),
            (
                direct_caught.exception.rubrique,
                direct_caught.exception.field,
                direct_caught.exception.offset,
                direct_caught.exception.value,
            ),
        )

    def test_dispatcher_module_has_no_odoo_runtime_import(self):
        self.assertNotIn("odoo", dispatcher.__dict__)
        self.assertNotIn("odoo", inspect.getsource(dispatcher))
