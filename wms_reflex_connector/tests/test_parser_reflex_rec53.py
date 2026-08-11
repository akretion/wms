# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import inspect
from dataclasses import fields
from decimal import Decimal

from odoo.tests.common import TransactionCase

import odoo.addons.wms_reflex_connector.parser_reflex.rec53 as rec53
from odoo.addons.wms_reflex_connector.parser_reflex.rec53 import (
    Reflex53ParseError,
    Reflex53Record,
    Reflex53Rubrique110,
    Reflex53Rubrique120,
    Reflex53Rubrique130,
    Reflex53Rubrique150,
    Reflex53Rubrique310,
    Reflex53Rubrique340,
    parse_record,
)


class TestReflex53Parser(TransactionCase):
    """Protocol-level tests using payloads assembled from the Interface 53 offsets."""

    COMMON = {
        "sequence": 1234567,
        "application": "HL",
        "interface": "53",
        "activity": " A",
        "physical_location": "L 1",
        "reception_year": "26",
        "reception_number": "REC 0001",
    }

    CLASSES = (
        Reflex53Rubrique110,
        Reflex53Rubrique120,
        Reflex53Rubrique130,
        Reflex53Rubrique150,
        Reflex53Rubrique310,
        Reflex53Rubrique340,
    )

    def _field_specs(self, rubrique):
        return {
            "110": (
                ("entry_date_century", 32, 2),
                ("entry_date_year", 34, 2),
                ("entry_date_month", 36, 2),
                ("entry_date_day", 38, 2),
                ("entry_time", 40, 6),
                ("reception_reason", 46, 3),
            ),
            "120": (
                ("ordering_party", 32, 13),
                ("customs_delay", 45, 3),
                ("workshop", 48, 3),
                ("reception_type", 51, 3),
            ),
            "130": (
                ("supplier", 32, 13),
                ("reception_reference", 45, 20),
                ("supplier_delivery_note", 65, 10),
            ),
            "150": (
                ("carrier", 32, 13),
                ("driver", 45, 20),
                ("transport_document", 65, 10),
                ("license_plate", 75, 10),
                ("arrival_date_century", 85, 2),
                ("arrival_date_year", 87, 2),
                ("arrival_date_month", 89, 2),
                ("arrival_date_day", 91, 2),
                ("arrival_time", 93, 6),
                ("appointment_date_century", 99, 2),
                ("appointment_date_year", 101, 2),
                ("appointment_date_month", 103, 2),
                ("appointment_date_day", 105, 2),
                ("appointment_start", 107, 6),
                ("appointment_end", 113, 6),
                ("confirmed_flag", 119, 1),
            ),
            "310": (
                ("reception_line", 32, 6),
                ("article", 38, 16),
                ("logistics_variant", 54, 2),
                ("logistics_variant_order_reference", 56, 16),
                ("supplier_packaging_reference", 72, 20),
                ("owner", 92, 3),
                ("quality", 95, 3),
            ),
            "340": (
                ("reception_line", 32, 6),
                ("quantity_level_1", 38, 7),
                ("quantity_level_2", 45, 7),
                ("quantity_level_3", 52, 7),
                ("quantity_base_vl", 59, 7),
                ("net_weight", 66, 9),
                ("gross_weight", 75, 9),
                ("volume", 84, 9),
                ("lot_1", 93, 20),
                ("manufacturing_date_century", 113, 2),
                ("manufacturing_date_year", 115, 2),
                ("manufacturing_date_month", 117, 2),
                ("manufacturing_date_day", 119, 2),
                ("best_before_date", 121, 8),
                ("sale_deadline_date", 129, 8),
                ("consumption_deadline_date", 137, 8),
                ("scheduling_date", 145, 8),
                ("missing_flag", 153, 1),
                ("missing_reason", 154, 3),
                ("lot_2", 157, 20),
                ("lot_3", 177, 20),
                ("control_flag", 197, 1),
                ("repackage_flag", 198, 1),
                ("special_block_flag", 199, 1),
                ("block_reason", 200, 3),
                ("detail_owner", 203, 3),
                ("detail_quality", 206, 3),
                ("reservation_recipient", 209, 13),
                ("reservation_recipient_family", 222, 15),
                ("reservation_reference", 237, 20),
                ("detail_reception_line_number", 257, 6),
            ),
        }[rubrique]

    def _payload(self, rubrique, values=None):
        """Build exactly 270 characters from one-based formal field offsets."""
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
        put(15, 3, values["activity"])
        put(18, 3, values["physical_location"])
        put(21, 2, values["reception_year"])
        put(23, 9, values["reception_number"])
        for name, offset, width in self._field_specs(rubrique):
            if name in values:
                put(offset, width, values[name])
        result = "".join(payload)
        self.assertEqual(len(result), 270)
        return result

    def _values_for(self, code):
        values = {}
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        widths = {name: width for name, _offset, width in self._field_specs(code)}
        for field in fields(next(cls for cls in self.CLASSES if cls.CODE == code)):
            if field.name in {f.name for f in fields(Reflex53Record)}:
                continue
            value = {
                "quantity_level_1": "0000012",
                "quantity_level_2": "0000003",
                "quantity_level_3": "0000004",
                "quantity_base_vl": "0000005",
                "net_weight": "000001234",
                "gross_weight": "000000002",
                "volume": "000000100",
            }.get(
                field.name,
                f"{alphabet[len(values)]}{field.name.upper()}",
            )
            values[field.name] = value[: widths[field.name]]
        return values

    def _assert_parse_error(self, parser, record, expected):
        with self.assertRaises(Reflex53ParseError) as context:
            parser(record)
        error = context.exception
        self.assertEqual(
            (error.rubrique, error.field, error.offset, error.value), expected
        )

    def test_all_layouts_fields_dispatch_and_direct_parse(self):
        for cls in self.CLASSES:
            with self.subTest(rubrique=cls.CODE):
                values = self._values_for(cls.CODE)
                record = self._payload(cls.CODE, values)
                direct = cls.parse(record)
                self.assertEqual(parse_record(record), direct)
                self.assertIsInstance(direct, cls)
                for name, offset, width in self._field_specs(cls.CODE):
                    self.assertEqual(
                        record[offset - 1 : offset - 1 + width],
                        str(values[name]).ljust(width),
                        name,
                    )
                for field in fields(cls):
                    self.assertTrue(hasattr(direct, field.name))
                common_values = {**self.COMMON, "rubrique": cls.CODE}
                for field in fields(Reflex53Record):
                    self.assertEqual(
                        getattr(direct, field.name), common_values[field.name]
                    )
                for field in fields(cls):
                    if field.name in {f.name for f in fields(Reflex53Record)}:
                        continue
                    expected = next(
                        record[offset - 1 : offset - 1 + width].rstrip(" ")
                        for name, offset, width in self._field_specs(cls.CODE)
                        if name == field.name
                    )
                    if cls.CODE == "340" and field.name.startswith("quantity_"):
                        expected = int(expected)
                    elif cls.CODE == "340" and field.name in {
                        "net_weight",
                        "gross_weight",
                        "volume",
                    }:
                        expected = Decimal(int(expected)).scaleb(-3)
                    self.assertEqual(getattr(direct, field.name), expected, field.name)
                    if (
                        "date" in field.name
                        or "time" in field.name
                        or field.name in {"appointment_start", "appointment_end"}
                    ):
                        self.assertIsInstance(getattr(direct, field.name), str)

    def test_340_numeric_values_blanks_and_exact_decimal(self):
        values = self._values_for("340")
        values.update(net_weight="000001234", gross_weight=" " * 9, volume="000000001")
        record = self._payload("340", values)
        parsed = Reflex53Rubrique340.parse(record)
        self.assertEqual(parsed.quantity_level_1, 12)
        self.assertEqual(parsed.quantity_level_2, 3)
        self.assertEqual(parsed.quantity_level_3, 4)
        self.assertEqual(parsed.quantity_base_vl, 5)
        self.assertEqual(parsed.net_weight, Decimal("1.234"))
        self.assertIsNone(parsed.gross_weight)
        self.assertEqual(parsed.volume, Decimal("0.001"))
        for name, _offset, _width in self._field_specs("340"):
            if "date" in name or "time" in name:
                self.assertIsInstance(getattr(parsed, name), str)

        for name, offset, width in (
            ("quantity_level_1", 38, 7),
            ("quantity_level_2", 45, 7),
            ("quantity_level_3", 52, 7),
            ("quantity_base_vl", 59, 7),
            ("net_weight", 66, 9),
            ("gross_weight", 75, 9),
            ("volume", 84, 9),
        ):
            bad = list(record)
            bad[offset - 1] = "X"
            with self.subTest(field=name):
                self._assert_parse_error(
                    Reflex53Rubrique340.parse,
                    "".join(bad),
                    (
                        "340",
                        name,
                        offset,
                        "".join(bad)[offset - 1 : offset - 1 + width],
                    ),
                )
        for name, width in (
            ("quantity_level_1", 7),
            ("quantity_level_2", 7),
            ("quantity_level_3", 7),
            ("quantity_base_vl", 7),
            ("net_weight", 9),
            ("gross_weight", 9),
            ("volume", 9),
        ):
            blank = self._values_for("340")
            blank[name] = " " * width
            with self.subTest(blank_field=name):
                self.assertIsNone(
                    getattr(
                        Reflex53Rubrique340.parse(self._payload("340", blank)), name
                    )
                )

    def test_spaces_are_preserved_except_right_padding(self):
        values = self._values_for("130")
        values.update(
            supplier=" Lead", reception_reference="A  B", supplier_delivery_note="END"
        )
        parsed = Reflex53Rubrique130.parse(self._payload("130", values))
        self.assertEqual(parsed.supplier, " Lead")
        self.assertEqual(parsed.reception_reference, "A  B")
        self.assertEqual(parsed.supplier_delivery_note, "END")

    def test_envelope_lengths_terminators_and_contextual_errors(self):
        record = self._payload("110", self._values_for("110"))
        self.assertEqual(
            Reflex53Rubrique110.parse(record + "\n"), Reflex53Rubrique110.parse(record)
        )
        self.assertEqual(
            Reflex53Rubrique110.parse(record + "\r\n"),
            Reflex53Rubrique110.parse(record),
        )
        for malformed, value in (
            (record[:-1], record[:-1]),
            (record + " ", record + " "),
            (record + "\r", record + "\r"),
            (record + "\n\n", record + "\n\n"),
            (record + "\r\n\r\n", record + "\r\n\r\n"),
        ):
            with self.subTest(malformed=repr(malformed[-4:])):
                self._assert_parse_error(
                    parse_record, malformed, (None, "record", 1, value)
                )
        for terminator in ("\r", "\n", "\r\n"):
            malformed = record[:100] + terminator + record[100:]
            self._assert_parse_error(
                parse_record, malformed, (None, "record", 1, malformed)
            )

        for offset, value, field in (
            (1, "X", "sequence"),
            (8, "XX", "application"),
            (10, "XX", "interface"),
            (12, "999", "rubrique"),
        ):
            bad = list(record)
            bad[offset - 1 : offset - 1 + len(value)] = value
            bad = "".join(bad)
            expected_rubrique = "999" if field == "rubrique" else "110"
            expected_value = bad[offset - 1 : offset - 1 + len(value)]
            self._assert_parse_error(
                parse_record,
                bad,
                (expected_rubrique, field, offset, expected_value),
            )

        bad = list(record)
        bad[48] = "X"
        bad = "".join(bad)
        self._assert_parse_error(
            Reflex53Rubrique110.parse,
            bad,
            ("110", "padding", 49, bad[48:270]),
        )
        padding = {
            "110": (49, 222),
            "120": (54, 217),
            "130": (75, 196),
            "150": (120, 151),
            "310": (98, 173),
            "340": (263, 8),
        }
        for cls in self.CLASSES:
            start, width = padding[cls.CODE]
            bad = list(self._payload(cls.CODE, self._values_for(cls.CODE)))
            bad[start - 1 + width - 1] = "X"
            bad = "".join(bad)
            self._assert_parse_error(
                cls.parse,
                bad,
                (cls.CODE, "padding", start, bad[start - 1 :]),
            )

    def test_wrong_expected_rubrique_and_positional_construction(self):
        record = self._payload("110", self._values_for("110"))
        self._assert_parse_error(
            Reflex53Rubrique120.parse,
            record,
            ("110", "rubrique", 12, "110"),
        )
        for cls in self.CLASSES:
            with self.subTest(rubrique=cls.CODE):
                with self.assertRaises(TypeError):
                    cls(record)

    def test_alternating_records_do_not_share_parser_state_or_models(self):
        records = [
            self._payload(code, self._values_for(code))
            for code in ("110", "340", "110", "340")
        ]
        parsed = [parse_record(record) for record in records]
        self.assertEqual(
            [item.rubrique for item in parsed], ["110", "340", "110", "340"]
        )
        source = inspect.getsource(rec53)
        self.assertNotIn("models.processor", source)
        self.assertNotIn("processor", rec53.__dict__)

        # Parsing remains independent of optional Odoo model imports.
        self.assertEqual(parse_record(records[1]).rubrique, "340")
