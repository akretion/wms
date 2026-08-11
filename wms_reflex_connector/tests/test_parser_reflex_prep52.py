# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dataclasses import fields
from decimal import Decimal

from odoo.tests.common import TransactionCase

from odoo.addons.wms_reflex_connector.parser_reflex.prep52 import (
    Reflex52ParseError,
    Reflex52Record,
    Reflex52Rubrique150,
    Reflex52Rubrique160,
    Reflex52Rubrique165,
    Reflex52Rubrique199,
    Reflex52Rubrique210,
    Reflex52Rubrique220,
    parse_record,
)


class TestReflex52PreparationParser(TransactionCase):
    COMMON = {
        "sequence": "0000123",
        "application": "HL",
        "interface": "52",
        "activity": " A",
        "physical_location": "L 1",
    }
    CLASSES = (
        Reflex52Rubrique150,
        Reflex52Rubrique160,
        Reflex52Rubrique165,
        Reflex52Rubrique199,
        Reflex52Rubrique210,
        Reflex52Rubrique220,
    )
    SPECS = {
        "150": (("preparation_year", 21, 2), ("preparation_number", 23, 9), ("validated_quantity_level_1", 32, 9), ("validated_quantity_level_2", 41, 9), ("validated_quantity_level_3", 50, 9), ("validated_quantity_base_vl", 59, 9), ("validated_general_quantity_level_1", 68, 9), ("validated_general_quantity_level_2", 77, 9), ("validated_total_net_weight", 86, 11), ("validated_total_gross_weight", 97, 11), ("validated_total_volume", 108, 11)),
        "160": (("preparation_year", 21, 2), ("preparation_number", 23, 9), ("stock_exit_date_century", 32, 2), ("stock_exit_date_year", 34, 2), ("stock_exit_date_month", 36, 2), ("stock_exit_date_day", 38, 2), ("stock_exit_time", 40, 6)),
        "165": (("preparation_year", 21, 2), ("preparation_number", 23, 9), ("loading_date_century", 32, 2), ("loading_date_year", 34, 2), ("loading_date_month", 36, 2), ("loading_date_day", 38, 2), ("loading_code", 40, 6), ("transport_means_type", 46, 6), ("carrier_code", 52, 13), ("carrier_loading_reference", 65, 20), ("driver_name", 85, 20), ("vehicle_registration", 105, 10), ("carrier_appointment_taken", 115, 1), ("carrier_appointment_date_century", 116, 2), ("carrier_appointment_date_year", 118, 2), ("carrier_appointment_date_month", 120, 2), ("carrier_appointment_date_day", 122, 2), ("carrier_appointment_time", 124, 6), ("carrier_arrival_date_century", 130, 2), ("carrier_arrival_date_year", 132, 2), ("carrier_arrival_date_month", 134, 2), ("carrier_arrival_date_day", 136, 2), ("carrier_arrival_time", 138, 6), ("carrier_departure_date_century", 144, 2), ("carrier_departure_date_year", 146, 2), ("carrier_departure_date_month", 148, 2), ("carrier_departure_date_day", 150, 2), ("carrier_departure_time", 152, 6), ("transport_summary_number", 158, 9), ("other_transport_document_reference", 167, 20), ("shipment_number", 187, 11)),
        "199": (("preparation_year", 21, 2), ("preparation_number", 23, 9), ("comment", 32, 70), ("comment_family", 102, 3)),
        "210": (("line_preparation_year", 21, 2), ("line_number", 23, 13), ("preparation_year", 36, 2), ("preparation_number", 38, 9), ("order_physical_location", 47, 3), ("order_year", 50, 2), ("order_number", 52, 9), ("order_line_number", 61, 7), ("article_code", 68, 16), ("article_logistics_variant_code", 84, 2), ("owner_code", 86, 3), ("quality_code", 89, 3), ("final_recipient_code", 92, 13), ("long_owner_code", 105, 13), ("ordering_party_reference", 118, 20), ("ordering_party_reference_line_number", 138, 7), ("recipient_article_reference", 145, 20), ("kit_code", 165, 1)),
        "220": (("line_preparation_year", 21, 2), ("line_number", 23, 13), ("preparation_year", 36, 2), ("preparation_number", 38, 9), ("odp_quantity_base_vl", 47, 7), ("odp_net_weight", 54, 9), ("line_quantity_base_vl", 63, 7), ("line_net_weight", 70, 9), ("validated_line_quantity_base_vl", 79, 7), ("validated_line_net_weight", 86, 9), ("generated_remainder_quantity_base_vl", 95, 7), ("generated_remainder_net_weight", 102, 9), ("substituted_quantity_numerator", 111, 7), ("substituted_quantity_denominator", 118, 7), ("substituted_net_weight", 125, 9)),
    }
    MINIMUMS = {"150": 118, "160": 45, "165": 197, "199": 104, "210": 165, "220": 133}
    INTEGER_FIELDS = {"validated_quantity_level_1", "validated_quantity_level_2", "validated_quantity_level_3", "validated_quantity_base_vl", "validated_general_quantity_level_1", "validated_general_quantity_level_2", "odp_quantity_base_vl", "line_quantity_base_vl", "validated_line_quantity_base_vl", "generated_remainder_quantity_base_vl", "substituted_quantity_numerator", "substituted_quantity_denominator"}
    DECIMAL_FIELDS = {"validated_total_net_weight", "validated_total_gross_weight", "validated_total_volume", "odp_net_weight", "line_net_weight", "validated_line_net_weight", "generated_remainder_net_weight", "substituted_net_weight"}

    def _payload(self, rubrique, values=None, length=270):
        payload = [" "] * length
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
        for name, offset, width in self.SPECS[rubrique]:
            if name in values:
                put(offset, width, values[name])
        return "".join(payload)

    def _values(self, rubrique):
        values = {}
        for index, (name, _offset, width) in enumerate(self.SPECS[rubrique], 1):
            if name in self.INTEGER_FIELDS:
                values[name] = "1".zfill(width)
            elif name in self.DECIMAL_FIELDS:
                values[name] = "1234".zfill(width)
            elif name == "kit_code":
                values[name] = "K"
            else:
                values[name] = (f"{index}{name.upper()}")[:width]
        return values

    def _assert_error(self, parser, record, expected):
        with self.assertRaises(Reflex52ParseError) as caught:
            parser(record)
        error = caught.exception
        self.assertEqual((error.rubrique, error.field, error.offset, error.value), expected)

    def test_every_workbook_field_direct_and_dispatch(self):
        for cls in self.CLASSES:
            with self.subTest(rubrique=cls.CODE):
                values = self._values(cls.CODE)
                record = self._payload(cls.CODE, values)
                parsed = cls.parse(record)
                self.assertEqual(parse_record(record), parsed)
                self.assertIsInstance(parsed, cls)
                self.assertEqual(parsed.sequence, 123)
                self.assertEqual(parsed.activity, " A")
                self.assertEqual(parsed.physical_location, "L 1")
                self.assertEqual(parsed.extension_data, "")
                for name, offset, width in self.SPECS[cls.CODE]:
                    raw = record[offset - 1 : offset - 1 + width]
                    expected = raw.rstrip(" ")
                    if name in self.INTEGER_FIELDS:
                        expected = int(expected)
                    elif name in self.DECIMAL_FIELDS:
                        expected = Decimal(int(expected)).scaleb(-3)
                    self.assertEqual(getattr(parsed, name), expected, name)
                self.assertEqual([item.name for item in fields(Reflex52Record)], ["sequence", "application", "interface", "rubrique", "activity", "physical_location", "extension_data"])

    def test_lengths_terminators_and_opaque_extensions(self):
        for code, minimum in self.MINIMUMS.items():
            with self.subTest(code=code):
                record = self._payload(code, self._values(code))
                self.assertEqual(parse_record(record[:minimum]).extension_data, "")
                extended = record[:minimum] + "EXT  "
                self.assertEqual(parse_record(extended).extension_data, "EXT")
                self.assertEqual(parse_record(record + "\n"), parse_record(record))
                self.assertEqual(parse_record(record + "\r\n"), parse_record(record))
                self._assert_error(parse_record, record[: minimum - 1], (code, "record", 1, record[: minimum - 1]))
        abilis = self._payload("210", self._values("210"), 165) + "FINAL-RECIPIENT-REFERENCE  "
        self.assertEqual(parse_record(abilis).extension_data, "FINAL-RECIPIENT-REFERENCE")
        record = self._payload("150", self._values("150"))
        self._assert_error(parse_record, record + "X", (None, "record", 1, record + "X"))
        self._assert_error(parse_record, record + "\r", (None, "record", 1, record + "\r"))
        self._assert_error(parse_record, record[:80] + "\n" + record[80:], (None, "record", 1, record[:80] + "\n" + record[80:]))

    def test_conversion_trimming_kit_and_contextual_failures(self):
        values = self._values("220")
        values.update(odp_quantity_base_vl=" " * 7, odp_net_weight="000001234", line_net_weight=" " * 9, article_code=" A  B")
        parsed = Reflex52Rubrique220.parse(self._payload("220", values))
        self.assertIsNone(parsed.odp_quantity_base_vl)
        self.assertEqual(parsed.odp_net_weight, Decimal("1.234"))
        self.assertIsNone(parsed.line_net_weight)
        self.assertEqual(parsed.preparation_number, values["preparation_number"])
        self._assert_error(Reflex52Rubrique220.parse, self._payload("220", {**values, "odp_quantity_base_vl": "000X001"}), ("220", "odp_quantity_base_vl", 47, "000X001"))
        for kit in ("", "K", "C"):
            self.assertEqual(Reflex52Rubrique210.parse(self._payload("210", {**self._values("210"), "kit_code": kit})).kit_code, kit)
        self._assert_error(Reflex52Rubrique210.parse, self._payload("210", {**self._values("210"), "kit_code": "X"}), ("210", "kit_code", 165, "X"))
        record = self._payload("160", self._values("160"))
        for offset, value, field, rubrique in ((1, "X", "sequence", "160"), (8, "XX", "application", "160"), (10, "XX", "interface", "160"), (12, "999", "rubrique", "999")):
            bad = record[: offset - 1] + value + record[offset - 1 + len(value) :]
            self._assert_error(parse_record, bad, (rubrique, field, offset, value))
        self._assert_error(Reflex52Rubrique160.parse, record[:11] + "150" + record[14:], ("150", "rubrique", 12, "150"))

    def test_keyword_only_dataclasses(self):
        for cls in (Reflex52Record, *self.CLASSES):
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(TypeError):
                    cls("not positional")
