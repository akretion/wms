# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal
from unittest import TestCase

from odoo.addons.wms_reflex_connector.parser_reflex import prep52
from odoo.addons.wms_reflex_connector.parser_reflex.dispatcher import (
    ReflexInterfaceDispatcher,
)


class TestReflex52MissingRubriques(TestCase):
    """Examples from Int52, data offsets starting after the 14-character header."""

    PREPARATION = "ACTDEP26000000123"
    LINE = "ACTDEP26000000000004226000000123"
    CLASSES = (
        prep52.Reflex52Rubrique010,
        prep52.Reflex52Rubrique110,
        prep52.Reflex52Rubrique120,
        prep52.Reflex52Rubrique130,
        prep52.Reflex52Rubrique140,
        prep52.Reflex52Rubrique230,
        prep52.Reflex52Rubrique240,
        prep52.Reflex52Rubrique250,
        prep52.Reflex52Rubrique251,
        prep52.Reflex52Rubrique260,
        prep52.Reflex52Rubrique299,
    )

    def _record(self, code, data):
        self.assertLessEqual(len(data), 256)
        return f"0000123HL52{code}{data:<256}"

    def _parse(self, cls, data):
        record = self._record(cls.CODE, data)
        result = cls.parse(record)
        self.assertEqual(prep52.parse_record(record), result)
        self.assertEqual(ReflexInterfaceDispatcher(("52",)).parse(record), result)
        self.assertIsInstance(result, cls)
        return result

    def test_units_do_not_become_activity_or_warehouse_codes(self):
        # 010, rows 15-22: eight unit codes, with no preparation identifiers.
        parsed = self._parse(prep52.Reflex52Rubrique010, "MM KM KG M3 M2 L  CELEUR")
        self.assertEqual(
            (
                parsed.length_unit,
                parsed.distance_unit,
                parsed.weight_unit,
                parsed.volume_unit,
                parsed.surface_unit,
                parsed.capacity_unit,
                parsed.temperature_unit,
                parsed.price_unit,
            ),
            ("MM", "KM", "KG", "M3", "M2", "L", "CEL", "EUR"),
        )
        self.assertEqual((parsed.activity, parsed.physical_location), ("", ""))

    def test_general_information_keeps_identifiers_and_scales_quantity(self):
        # 110, rows 17-24: transport quantity is 11 digits, three decimals.
        parsed = self._parse(
            prep52.Reflex52Rubrique110,
            self.PREPARATION
            + "STD"
            + "PREP-CLIENT".ljust(13)
            + "SHIP-CLIENT".ljust(13)
            + "00000001234"
            + "PAL"
            + "VEN",
        )
        self.assertEqual((parsed.activity, parsed.physical_location), ("ACT", "DEP"))
        self.assertEqual(parsed.preparation_year, "26")
        self.assertEqual(parsed.preparation_number, "000000123")
        self.assertEqual(parsed.preparation_type_code, "STD")
        self.assertEqual(parsed.preparation_recipient_code, "PREP-CLIENT")
        self.assertEqual(parsed.shipment_recipient_code, "SHIP-CLIENT")
        self.assertEqual(parsed.transport_quantity, Decimal("1.234"))
        self.assertEqual(parsed.transport_quantity_unit, "PAL")
        self.assertEqual(parsed.preparation_order_reason_code, "VEN")

    def test_delivery_and_appointment_have_four_digit_time_windows(self):
        # 120/130, rows 19-24: the time windows use HHMM, not HHMMSS.
        for cls, prefix in (
            (prep52.Reflex52Rubrique120, "expected_delivery"),
            (prep52.Reflex52Rubrique130, "appointment"),
        ):
            with self.subTest(code=cls.CODE):
                parsed = self._parse(cls, self.PREPARATION + "2026102108301745")
                self.assertEqual(getattr(parsed, f"{prefix}_date_century"), "20")
                self.assertEqual(getattr(parsed, f"{prefix}_date_year"), "26")
                self.assertEqual(getattr(parsed, f"{prefix}_date_month"), "10")
                self.assertEqual(getattr(parsed, f"{prefix}_date_day"), "21")
                self.assertEqual(getattr(parsed, f"{prefix}_start_time"), "0830")
                self.assertEqual(getattr(parsed, f"{prefix}_end_time"), "1745")

    def test_preparation_totals_preserve_distinct_quantity_levels(self):
        # 140, rows 19-27: six counts followed by net/gross weight and volume.
        parsed = self._parse(
            prep52.Reflex52Rubrique140,
            self.PREPARATION
            + "000000001000000002000000003000000004000000005000000006"
            + "000000012340000000567800000009012",
        )
        self.assertEqual(
            (
                parsed.quantity_level_1,
                parsed.quantity_level_2,
                parsed.quantity_level_3,
                parsed.quantity_base_vl,
                parsed.general_quantity_level_1,
                parsed.general_quantity_level_2,
            ),
            (1, 2, 3, 4, 5, 6),
        )
        self.assertEqual(parsed.total_net_weight, Decimal("1.234"))
        self.assertEqual(parsed.total_gross_weight, Decimal("5.678"))
        self.assertEqual(parsed.total_volume, Decimal("9.012"))

    def test_validation_and_remainder_keep_line_identity(self):
        validated = self._parse(
            prep52.Reflex52Rubrique230, self.LINE + "00720261020083015"
        )
        self.assertEqual(validated.line_preparation_year, "26")
        self.assertEqual(validated.line_number, "0000000000042")
        self.assertEqual(validated.forced_scheduling_minimum_days, 7)
        self.assertEqual(validated.validation_date_century, "20")
        self.assertEqual(validated.validation_date_year, "26")
        self.assertEqual(validated.validation_date_month, "10")
        self.assertEqual(validated.validation_date_day, "20")
        self.assertEqual(validated.validation_time, "083015")
        remainder = self._parse(
            prep52.Reflex52Rubrique240, self.LINE + "REMDEP270000000000084"
        )
        self.assertEqual(remainder.remainder_activity, "REM")
        self.assertEqual(remainder.remainder_physical_location, "DEP")
        self.assertEqual(remainder.remainder_line_preparation_year, "27")
        self.assertEqual(remainder.remainder_line_number, "0000000000084")
        self.assertEqual(remainder.preparation_number, "000000123")

    def test_outgoing_gei_quantities_lots_dates_and_identifiers(self):
        # 250, rows 21-51, including the numeric XLS cell "9.3" for net weight.
        parsed = self._parse(
            prep52.Reflex52Rubrique250,
            self.LINE + "0000012"
            "000012345" + "SUPPLIER".ljust(13) + "000000000000000123"
            "000000000000000456"
            "00000007890" + " LOT 1".ljust(20) + "20260102"
            "20260203"
            "20270304"
            "20270405"
            "20270506" + "LOT-2".ljust(20) + "LOT-3".ljust(20) + "PALBOX",
        )
        self.assertEqual(parsed.quantity_base_vl, 12)
        self.assertEqual(parsed.net_weight, Decimal("12.345"))
        self.assertEqual(parsed.price, Decimal("7.890"))
        self.assertEqual(parsed.supplier_code, "SUPPLIER")
        self.assertEqual(parsed.support_number, "000000000000000123")
        self.assertEqual(parsed.parcel_number, "000000000000000456")
        self.assertEqual(
            (parsed.lot_1, parsed.lot_2, parsed.lot_3), (" LOT 1", "LOT-2", "LOT-3")
        )
        for prefix, expected in (
            ("manufacturing", "20260102"),
            ("receipt", "20260203"),
            ("best_before", "20270304"),
            ("sell_by", "20270405"),
            ("use_by", "20270506"),
        ):
            self.assertEqual(
                "".join(
                    getattr(parsed, f"{prefix}_date_{part}")
                    for part in ("century", "year", "month", "day")
                ),
                expected,
            )
        self.assertEqual(
            (parsed.support_type_code, parsed.parcel_type_code), ("PAL", "BOX")
        )

    def test_blocking_and_reservation_respect_reserved_zones(self):
        # 251, rows 21-42: reserved zones are opaque and do not shift flags.
        parsed = self._parse(
            prep52.Reflex52Rubrique251,
            self.LINE + "1BLK1"
            "20261021"
            "AB  "
            "0"
            "20261022"
            " CD "
            "10"
            + "RECIPIENT".ljust(13)
            + "FAMILY".ljust(15)
            + "RESERVATION".ljust(20)
            + "ORDERER".ljust(13)
            + "ALLOCATION".ljust(20)
            + "1",
        )
        self.assertEqual(parsed.blocked_specific_reason_flag, "1")
        self.assertEqual(parsed.blocking_reason_code, "BLK")
        self.assertEqual(parsed.blocked_customs_flag, "1")
        self.assertEqual(parsed.customs_release_date_day, "21")
        self.assertEqual(parsed.customs_reserved, "AB")
        self.assertEqual(parsed.blocked_stabilization_flag, "0")
        self.assertEqual(parsed.stabilization_release_date_day, "22")
        self.assertEqual(parsed.stabilization_reserved, " CD")
        self.assertEqual(parsed.blocked_control_flag, "1")
        self.assertEqual(parsed.blocked_reconditioning_flag, "0")
        self.assertEqual(parsed.reservation_recipient_code, "RECIPIENT")
        self.assertEqual(parsed.reservation_recipient_family_code, "FAMILY")
        self.assertEqual(parsed.reservation_reference, "RESERVATION")
        self.assertEqual(parsed.allocation_ordering_party_code, "ORDERER")
        self.assertEqual(parsed.allocation_order_reference, "ALLOCATION")
        self.assertEqual(parsed.already_prepared_flag, "1")

    def test_serial_range_and_line_comment(self):
        serials = self._parse(
            prep52.Reflex52Rubrique260,
            self.LINE + "00001".ljust(30) + "00012".ljust(30) + "00012",
        )
        self.assertEqual(serials.start_serial_number, "00001")
        self.assertEqual(serials.end_serial_number, "00012")
        self.assertEqual(serials.entered_unit_count, 12)
        comment = self._parse(
            prep52.Reflex52Rubrique299,
            self.LINE + " Livrer  avec soin".ljust(70) + "LIV",
        )
        self.assertEqual(comment.comment, " Livrer  avec soin")
        self.assertEqual(comment.comment_family, "LIV")
        self.assertEqual(comment.line_number, "0000000000042")

    def test_optional_numbers_accept_blank_and_zero_but_reject_invalid_values(self):
        # One example for every new numeric format (width and decimal scale).
        for cls, offset, width, field, zero in (
            (prep52.Reflex52Rubrique110, 61, 11, "transport_quantity", Decimal(0)),
            (prep52.Reflex52Rubrique140, 32, 9, "quantity_level_1", 0),
            (prep52.Reflex52Rubrique230, 47, 3, "forced_scheduling_minimum_days", 0),
            (prep52.Reflex52Rubrique250, 47, 7, "quantity_base_vl", 0),
            (prep52.Reflex52Rubrique250, 54, 9, "net_weight", Decimal(0)),
            (prep52.Reflex52Rubrique260, 107, 5, "entered_unit_count", 0),
        ):
            with self.subTest(code=cls.CODE, field=field):
                blank = self._record(cls.CODE, "")
                self.assertIsNone(getattr(cls.parse(blank), field))
                for raw in (
                    "0" * width,
                    "0" * (width - 1) + "X",
                    " " * (width - 1) + "1",
                ):
                    record = blank[: offset - 1] + raw + blank[offset - 1 + width :]
                    if raw == "0" * width:
                        self.assertEqual(getattr(cls.parse(record), field), zero)
                    else:
                        with self.assertRaises(prep52.Reflex52ParseError) as caught:
                            ReflexInterfaceDispatcher(("52",)).parse(record)
                        error = caught.exception
                        self.assertEqual(
                            (error.rubrique, error.field, error.offset, error.value),
                            (cls.CODE, field, offset, raw),
                        )

    def test_all_new_rubriques_dispatch_with_line_terminators(self):
        for cls in self.CLASSES:
            with self.subTest(code=cls.CODE):
                record = self._record(cls.CODE, "")
                expected = cls.parse(record)
                self.assertEqual(prep52.parse_record(record), expected)
                for terminator in ("\n", "\r\n"):
                    self.assertEqual(
                        ReflexInterfaceDispatcher(("52",)).parse(record + terminator),
                        expected,
                    )
