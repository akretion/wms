# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dataclasses import fields

from odoo.tests.common import TransactionCase

import odoo.addons.wms_reflex_connector.parser_reflex.gei62 as gei62
from odoo.addons.wms_reflex_connector.parser_reflex.gei62 import (
    Reflex62ParseError,
    Reflex62Record,
    Reflex62Rubrique110,
    Reflex62Rubrique112,
    parse_record,
)


class TestReflex62GeiParser(TransactionCase):
    """Protocol-level tests using Interface 62 one-based fixed-width offsets."""

    COMMON = {
        "sequence": "0000123",
        "application": "HL",
        "interface": "62",
    }

    FIELD_SPECS = {
        "110": (
            ("physical_location", 15, 3),
            ("movement_year", 21, 2),
            ("movement_number", 23, 9),
            ("movement_direction", 32, 1),
            ("stock_type", 33, 3),
            ("gei_movement_type", 36, 3),
            ("stock_movement_type", 39, 3),
            ("stock_movement_reference", 55, 20),
            ("miscellaneous_reason", 75, 3),
            ("article", 146, 16),
            ("quality", 167, 3),
            ("movement_quantity_base_vl", 170, 9),
        ),
        "112": (("creation_date", 176, 8),),
    }

    def _payload(self, rubrique, values=None):
        """Build exactly 270 characters from the formal full-line offsets."""
        payload = [" "] * 270
        values = {**self.COMMON, **(values or {})}

        def put(offset, width, value):
            value = str(value)
            self.assertLessEqual(len(value), width)
            payload[offset - 1 : offset - 1 + width] = list(value.ljust(width))

        put(1, 7, values["sequence"])
        put(8, 2, values["application"])
        put(10, 2, values["interface"])
        put(12, 3, rubrique)
        for name, offset, width in self.FIELD_SPECS.get(rubrique, ()):
            if name in values:
                put(offset, width, values[name])
        result = "".join(payload)
        self.assertEqual(len(result), 270)
        return result

    def _put_exact(self, record, offset, width, value):
        result = list(record)
        self.assertEqual(len(value), width)
        result[offset - 1 : offset - 1 + width] = list(value)
        return "".join(result)

    def _assert_parse_error(self, parser, record, expected):
        with self.assertRaises(Reflex62ParseError) as context:
            parser(record)
        error = context.exception
        self.assertEqual(
            (error.rubrique, error.field, error.offset, error.value), expected
        )

    def test_110_exposes_every_field_at_its_exact_offset(self):
        values = {
            "physical_location": " A1",
            "movement_year": "26",
            "movement_number": "000004201",
            "movement_direction": "S",
            "stock_type": "DIS",
            "gei_movement_type": "M01",
            "stock_movement_type": "OUT",
            "stock_movement_reference": " REF  00042",
            "miscellaneous_reason": "*X",
            "article": "0000000000001234",
            "quality": " Q1",
            "movement_quantity_base_vl": "000001234",
        }
        record = self._payload("110", values)
        for name, offset, width in self.FIELD_SPECS["110"]:
            self.assertEqual(
                record[offset - 1 : offset - 1 + width],
                str(values[name]).ljust(width),
            )
        for offset, width in ((18, 3), (42, 13), (78, 68), (162, 5), (179, 69)):
            record = self._put_exact(record, offset, width, "X" * width)

        parsed = Reflex62Rubrique110.parse(record)
        self.assertEqual(parse_record(record), parsed)
        self.assertIsInstance(parsed, Reflex62Rubrique110)
        self.assertEqual(parsed.sequence, 123)
        self.assertEqual(parsed.application, "HL")
        self.assertEqual(parsed.interface, "62")
        self.assertEqual(parsed.rubrique, "110")
        self.assertEqual(parsed.physical_location, " A1")
        self.assertEqual(parsed.movement_year, "26")
        self.assertEqual(parsed.movement_number, "000004201")
        self.assertEqual(parsed.movement_direction, "S")
        self.assertEqual(parsed.stock_type, "DIS")
        self.assertEqual(parsed.gei_movement_type, "M01")
        self.assertEqual(parsed.stock_movement_type, "OUT")
        self.assertEqual(parsed.stock_movement_reference, " REF  00042")
        self.assertEqual(parsed.miscellaneous_reason, "*X")
        self.assertEqual(parsed.article, "0000000000001234")
        self.assertEqual(parsed.quality, " Q1")
        self.assertEqual(parsed.movement_quantity_base_vl, 1234)
        self.assertEqual(record[247:270], " " * 23)
        self.assertNotIn("processor", gei62.__dict__)

    def test_110_right_padding_and_optional_quantity(self):
        values = {
            "physical_location": " A",
            "movement_year": "6",
            "movement_number": "0001",
            "movement_direction": "I",
            "stock_type": "S",
            "gei_movement_type": "G",
            "stock_movement_type": "T",
            "stock_movement_reference": "R  E",
            "miscellaneous_reason": "R",
            "article": "00012",
            "quality": "Q",
            "movement_quantity_base_vl": " " * 9,
        }
        parsed = Reflex62Rubrique110.parse(self._payload("110", values))
        self.assertEqual(parsed.physical_location, " A")
        self.assertEqual(parsed.movement_year, "6")
        self.assertEqual(parsed.movement_number, "0001")
        self.assertEqual(parsed.stock_movement_reference, "R  E")
        self.assertEqual(parsed.article, "00012")
        self.assertIsNone(parsed.movement_quantity_base_vl)

    def test_112_exposes_creation_date_and_ignores_non_padding_ranges(self):
        record = self._payload("112", {"creation_date": "26081109"})
        record = self._put_exact(record, 15, 161, "I" * 161)
        record = self._put_exact(record, 184, 26, "J" * 26)
        parsed = Reflex62Rubrique112.parse(record)
        self.assertEqual(parse_record(record), parsed)
        self.assertIsInstance(parsed, Reflex62Rubrique112)
        self.assertEqual(parsed.sequence, 123)
        self.assertEqual(parsed.application, "HL")
        self.assertEqual(parsed.interface, "62")
        self.assertEqual(parsed.rubrique, "112")
        self.assertEqual(parsed.creation_date, "26081109")
        self.assertEqual(record[209:270], " " * 61)

    def test_framing_envelope_dispatch_and_contextual_errors(self):
        record = self._payload("110", {"movement_quantity_base_vl": "000000001"})
        self.assertEqual(parse_record(record + "\n"), parse_record(record))
        self.assertEqual(parse_record(record + "\r\n"), parse_record(record))
        for malformed in (record[:-1], record + " ", record + "\r", record + "\n\n"):
            with self.subTest(malformed=repr(malformed[-4:])):
                self._assert_parse_error(
                    parse_record, malformed, (None, "record", 1, malformed)
                )
        embedded = record[:100] + "\n" + record[100:]
        self._assert_parse_error(parse_record, embedded, (None, "record", 1, embedded))
        for offset, value, width, field, rubrique in (
            (1, "X", 7, "sequence", "110"),
            (8, "XX", 2, "application", "110"),
            (10, "XX", 2, "interface", "110"),
            (12, "010", 3, "rubrique", "010"),
            (12, "111", 3, "rubrique", "111"),
        ):
            with self.subTest(field=field, value=value):
                bad = self._put_exact(record, offset, len(value), value)
                self._assert_parse_error(
                    parse_record,
                    bad,
                    (rubrique, field, offset, bad[offset - 1 : offset - 1 + width]),
                )
        self._assert_parse_error(
            Reflex62Rubrique112.parse,
            record,
            ("110", "rubrique", 12, "110"),
        )

    def test_field_validation_padding_and_keyword_only_construction(self):
        record_110 = self._payload("110", {"movement_quantity_base_vl": "000000001"})
        bad_quantity = self._put_exact(record_110, 170, 9, "0000X0001")
        self._assert_parse_error(
            Reflex62Rubrique110.parse,
            bad_quantity,
            ("110", "movement_quantity_base_vl", 170, "0000X0001"),
        )
        bad_110_padding = self._put_exact(record_110, 248, 23, "X" + " " * 22)
        self._assert_parse_error(
            Reflex62Rubrique110.parse,
            bad_110_padding,
            ("110", "padding", 248, "X" + " " * 22),
        )
        record_112 = self._payload("112", {"creation_date": "26081109"})
        bad_date = self._put_exact(record_112, 176, 8, "26081A09")
        self._assert_parse_error(
            Reflex62Rubrique112.parse,
            bad_date,
            ("112", "creation_date", 176, "26081A09"),
        )
        bad_112_padding = self._put_exact(record_112, 210, 61, "X" + " " * 60)
        self._assert_parse_error(
            Reflex62Rubrique112.parse,
            bad_112_padding,
            ("112", "padding", 210, "X" + " " * 60),
        )
        for cls in (Reflex62Record, Reflex62Rubrique110, Reflex62Rubrique112):
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(TypeError):
                    cls(record_110)
        self.assertEqual(
            [field.name for field in fields(Reflex62Record)],
            ["sequence", "application", "interface", "rubrique"],
        )
