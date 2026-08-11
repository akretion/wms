# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dataclasses import fields
from decimal import Decimal

from odoo.tests.common import TransactionCase

import odoo.addons.wms_reflex_connector.parser_reflex.stock55 as stock55
from odoo.addons.wms_reflex_connector.parser_reflex.stock55 import (
    Reflex55ParseError,
    Reflex55Record,
    Reflex55Rubrique110,
    parse_record,
)


class TestReflex55StockDetailParser(TransactionCase):
    """Protocol tests assembled from Interface 55 one-based workbook offsets."""

    COMMON = {"sequence": "0000123", "application": "HL", "interface": "55"}
    FIELD_SPECS = (
        ("physical_depot_code", 15, 3, "text"), ("stock_type_code", 18, 3, "text"),
        ("activity_code", 21, 3, "text"), ("article_code", 24, 16, "text"),
        ("article_logistics_variant_code", 40, 2, "text"), ("owner_code", 42, 3, "text"),
        ("quality_code", 45, 3, "text"), ("available_for_preparation_flag", 48, 1, "text"),
        ("blocked_special_reason_flag", 49, 1, "text"), ("blocking_reason_code", 50, 3, "text"),
        ("blocked_customs_flag", 53, 1, "text"), ("blocked_stabilization_flag", 54, 1, "text"),
        ("blocked_control_flag", 55, 1, "text"), ("blocked_reconditioning_flag", 56, 1, "text"),
        ("blocked_exit_location_flag", 57, 1, "text"), ("blocked_inventory_flag", 58, 1, "text"),
        ("supplier_code", 59, 13, "text"), ("lot_1", 72, 20, "text"),
        ("scheduling_date_century", 92, 2, "text"), ("scheduling_date_year", 94, 2, "text"),
        ("scheduling_date_month", 96, 2, "text"), ("scheduling_date_day", 98, 2, "text"),
        ("manufacturing_date_century", 100, 2, "text"), ("manufacturing_date_year", 102, 2, "text"),
        ("manufacturing_date_month", 104, 2, "text"), ("manufacturing_date_day", 106, 2, "text"),
        ("reception_date_century", 108, 2, "text"), ("reception_date_year", 110, 2, "text"),
        ("reception_date_month", 112, 2, "text"), ("reception_date_day", 114, 2, "text"),
        ("sale_deadline_date_century", 116, 2, "text"), ("sale_deadline_date_year", 118, 2, "text"),
        ("sale_deadline_date_month", 120, 2, "text"), ("sale_deadline_date_day", 122, 2, "text"),
        ("consumption_deadline_date_century", 124, 2, "text"), ("consumption_deadline_date_year", 126, 2, "text"),
        ("consumption_deadline_date_month", 128, 2, "text"), ("consumption_deadline_date_day", 130, 2, "text"),
        ("best_before_date_century", 132, 2, "text"), ("best_before_date_year", 134, 2, "text"),
        ("best_before_date_month", 136, 2, "text"), ("best_before_date_day", 138, 2, "text"),
        ("quantity_base_vl", 140, 9, "int"), ("net_weight", 149, 9, "decimal"),
        ("generation_date_century", 158, 2, "text"), ("generation_date_year", 160, 2, "text"),
        ("generation_date_month", 162, 2, "text"), ("generation_date_day", 164, 2, "text"),
        ("generation_time", 166, 6, "text"), ("reservation_recipient_code", 172, 13, "text"),
        ("reservation_recipient_family_code", 185, 15, "text"), ("at_picking_flag", 200, 1, "text"),
        ("lot_2", 201, 20, "text"), ("lot_3", 221, 20, "text"),
        ("odp_reservation_reference", 241, 20, "text"),
    )

    def _payload(self, values=None, rubrique="110"):
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
        for name, offset, width, _kind in self.FIELD_SPECS:
            if name in values:
                put(offset, width, values[name])
        return "".join(payload)

    def _put_exact(self, record, offset, width, value):
        self.assertEqual(len(value), width)
        result = list(record)
        result[offset - 1 : offset - 1 + width] = list(value)
        return "".join(result)

    def _assert_error(self, parser, record, expected):
        with self.assertRaises(Reflex55ParseError) as caught:
            parser(record)
        self.assertEqual(
            (caught.exception.rubrique, caught.exception.field, caught.exception.offset,
             caught.exception.value),
            expected,
        )

    def test_110_exposes_all_workbook_fields_at_exact_offsets(self):
        values = {
            name: ("000001234" if kind == "int" else "000012345" if kind == "decimal"
                   else " A B" if name == "physical_depot_code" else "L  1" if name == "lot_1"
                   else f"V{index:02d}")
            for index, (name, _offset, width, kind) in enumerate(self.FIELD_SPECS, 1)
        }
        values.update({name: value[:width] for name, _offset, width, _kind in self.FIELD_SPECS
                       for value in (values[name],)})
        record = self._payload(values)
        parsed = Reflex55Rubrique110.parse(record)
        self.assertEqual(parse_record(record), parsed)
        self.assertIsInstance(parsed, Reflex55Rubrique110)
        self.assertEqual((parsed.sequence, parsed.application, parsed.interface, parsed.rubrique),
                         (123, "HL", "55", "110"))
        for name, offset, width, kind in self.FIELD_SPECS:
            raw = record[offset - 1 : offset - 1 + width]
            self.assertEqual(raw, values[name].ljust(width))
            expected = (1234 if kind == "int" else Decimal("12.345") if kind == "decimal"
                        else values[name].rstrip(" "))
            self.assertEqual(getattr(parsed, name), expected)
        self.assertEqual(parsed.physical_depot_code, " A")
        self.assertEqual(parsed.lot_1, "L  1")
        self.assertEqual(record[260:270], " " * 10)
        self.assertNotIn("processor", stock55.__dict__)

    def test_optional_numbers_text_trimming_and_unvalidated_business_values(self):
        values = {"quantity_base_vl": " " * 9, "net_weight": " " * 9,
                  "available_for_preparation_flag": "?", "scheduling_date_month": "ZZ",
                  "generation_time": "X Y"}
        parsed = Reflex55Rubrique110.parse(self._payload(values))
        self.assertIsNone(parsed.quantity_base_vl)
        self.assertIsNone(parsed.net_weight)
        self.assertEqual(parsed.available_for_preparation_flag, "?")
        self.assertEqual(parsed.scheduling_date_month, "ZZ")
        self.assertEqual(parsed.generation_time, "X Y")

    def test_framing_envelope_dispatch_padding_and_numeric_errors(self):
        record = self._payload({"quantity_base_vl": "000000001", "net_weight": "000000001"})
        self.assertEqual(parse_record(record + "\n"), parse_record(record))
        self.assertEqual(parse_record(record + "\r\n"), parse_record(record))
        for malformed in (record[:-1], record + " ", record + "\r", record + "\n\n",
                          record[:100] + "\n" + record[100:]):
            with self.subTest(malformed=repr(malformed[-4:])):
                self._assert_error(parse_record, malformed, (None, "record", 1, malformed))
        for offset, value, width, field, rubrique in (
            (1, "X" * 7, 7, "sequence", "110"), (8, "XX", 2, "application", "110"),
            (10, "XX", 2, "interface", "110"), (12, "010", 3, "rubrique", "010"),
            (140, "0000X0001", 9, "quantity_base_vl", "110"),
            (149, "0000\u06610001", 9, "net_weight", "110"),
            (261, "X" + " " * 9, 10, "padding", "110"),
        ):
            bad = self._put_exact(record, offset, width, value)
            self._assert_error(parse_record, bad, (rubrique, field, offset, value))
        self._assert_error(Reflex55Rubrique110.parse, self._payload(rubrique="111"),
                           ("111", "rubrique", 12, "111"))
        for cls in (Reflex55Record, Reflex55Rubrique110):
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(TypeError):
                    cls(record)
        self.assertEqual([field.name for field in fields(Reflex55Record)],
                         ["sequence", "application", "interface", "rubrique"])
