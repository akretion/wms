"""Pure fixed-width parser for Reflex Interface 52 preparation records."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Self

_SUPPORTED = (
    "010",
    "110",
    "120",
    "130",
    "140",
    "150",
    "160",
    "165",
    "199",
    "210",
    "220",
    "230",
    "240",
    "250",
    "251",
    "260",
    "299",
)

_MINIMUM_LENGTHS = {
    "010": 38,
    "110": 77,
    "120": 47,
    "130": 47,
    "140": 118,
    "150": 118,
    "160": 45,
    "165": 197,
    "199": 104,
    "210": 165,
    "220": 133,
    "230": 63,
    "240": 67,
    "250": 228,
    "251": 160,
    "260": 111,
    "299": 119,
}


class Reflex52ParseError(ValueError):
    """A malformed Interface 52 record, with protocol location context."""

    def __init__(
        self, message: str, *, rubrique: str | None, field: str, offset: int, value: str
    ) -> None:
        super().__init__(message)
        self.rubrique = rubrique
        self.field = field
        self.offset = offset
        self.value = value


def _error(
    rubrique: str | None, field: str, offset: int, value: str, reason: str
) -> Reflex52ParseError:
    return Reflex52ParseError(
        f"Interface 52 {field} at offset {offset}: {reason} ({value!r})",
        rubrique=rubrique,
        field=field,
        offset=offset,
        value=value,
    )


def _normalise_payload(record: str) -> str:
    if not isinstance(record, str):
        raise _error(None, "record", 1, repr(record), "record must be text")
    payload = (
        record[:-2]
        if record.endswith("\r\n")
        else record[:-1]
        if record.endswith("\n")
        else record
    )
    if "\r" in payload or "\n" in payload or len(payload) < 14:
        raise _error(
            None,
            "record",
            1,
            record,
            "unexpected line terminator or invalid record length",
        )
    return payload


def _field(
    payload: str, offset: int, width: int, rubrique: str | None, field: str
) -> str:
    raw = payload[offset - 1 : offset - 1 + width]
    return raw


def _text(payload: str, offset: int, width: int, rubrique: str, field: str) -> str:
    return _field(payload, offset, width, rubrique, field).rstrip(" ")


def _optional_int(raw: str, rubrique: str, field: str, offset: int) -> int | None:
    if not raw.strip(" "):
        return None
    if not raw.isascii() or not raw.isdigit():
        raise _error(rubrique, field, offset, raw, "expected ASCII digits")
    return int(raw)


def _optional_decimal_9_3(
    raw: str, rubrique: str, field: str, offset: int
) -> Decimal | None:
    if not raw.strip(" "):
        return None
    if not raw.isascii() or not raw.isdigit():
        raise _error(rubrique, field, offset, raw, "expected ASCII digits")
    return Decimal(int(raw)).scaleb(-3)


def _envelope(payload: str) -> tuple[str, dict[str, Any]]:
    candidate = payload[11:14]
    sequence = _field(payload, 1, 7, candidate, "sequence")
    if not sequence.isascii() or not sequence.isdigit():
        raise _error(candidate, "sequence", 1, sequence, "expected ASCII digits")
    application = _field(payload, 8, 2, candidate, "application")
    if application != "HL":
        raise _error(candidate, "application", 8, application, "expected 'HL'")
    interface = _field(payload, 10, 2, candidate, "interface")
    if interface != "52":
        raise _error(candidate, "interface", 10, interface, "expected '52'")
    rubrique = _field(payload, 12, 3, candidate, "rubrique")
    if rubrique not in _SUPPORTED:
        return None, None
    return rubrique, {
        "sequence": int(sequence),
        "application": application,
        "interface": interface,
        "rubrique": rubrique,
        # Rubrique 010 contains units, without activity or warehouse identifiers.
        "activity": (
            "" if rubrique == "010" else _text(payload, 15, 3, rubrique, "activity")
        ),
        "physical_location": (
            ""
            if rubrique == "010"
            else _text(payload, 18, 3, rubrique, "physical_location")
        ),
    }


def _prepare(record: str, expected: str) -> tuple[str, dict[str, Any]]:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    if rubrique != expected:
        raise _error(rubrique, "rubrique", 12, rubrique, f"expected '{expected}'")
    return payload, values


def _values(
    payload: str, cls: type["Reflex52Record"], values: dict[str, Any]
) -> dict[str, Any]:
    for name, offset, width, converter in cls.FIELDS:
        raw = _field(payload, offset, width, cls.CODE, name)
        if converter == "int":
            values[name] = _optional_int(raw, cls.CODE, name, offset)
        elif converter == "decimal":
            values[name] = _optional_decimal_9_3(raw, cls.CODE, name, offset)
        elif converter == "kit":
            values[name] = raw.rstrip(" ")
        else:
            values[name] = raw.rstrip(" ")
    values["extension_data"] = payload[_MINIMUM_LENGTHS[cls.CODE] :].rstrip(" ")
    return values


@dataclass(kw_only=True)
class Reflex52UnknownRecord:
    CODE: ClassVar[str] = None


@dataclass(kw_only=True)
class Reflex52Record:
    sequence: int
    application: str
    interface: str
    rubrique: str
    activity: str
    physical_location: str
    extension_data: str


@dataclass(kw_only=True)
class Reflex52Rubrique010(Reflex52Record):
    length_unit: str
    distance_unit: str
    weight_unit: str
    volume_unit: str
    surface_unit: str
    capacity_unit: str
    temperature_unit: str
    price_unit: str
    CODE: ClassVar[str] = "010"
    FIELDS: ClassVar[tuple] = (
        ("length_unit", 15, 3, "text"),
        ("distance_unit", 18, 3, "text"),
        ("weight_unit", 21, 3, "text"),
        ("volume_unit", 24, 3, "text"),
        ("surface_unit", 27, 3, "text"),
        ("capacity_unit", 30, 3, "text"),
        ("temperature_unit", 33, 3, "text"),
        ("price_unit", 36, 3, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique110(Reflex52Record):
    preparation_year: str
    preparation_number: str
    preparation_type_code: str
    preparation_recipient_code: str
    shipment_recipient_code: str
    transport_quantity: Decimal | None
    transport_quantity_unit: str
    preparation_order_reason_code: str
    CODE: ClassVar[str] = "110"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("preparation_type_code", 32, 3, "text"),
        ("preparation_recipient_code", 35, 13, "text"),
        ("shipment_recipient_code", 48, 13, "text"),
        ("transport_quantity", 61, 11, "decimal"),
        ("transport_quantity_unit", 72, 3, "text"),
        ("preparation_order_reason_code", 75, 3, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique120(Reflex52Record):
    preparation_year: str
    preparation_number: str
    expected_delivery_date_century: str
    expected_delivery_date_year: str
    expected_delivery_date_month: str
    expected_delivery_date_day: str
    expected_delivery_start_time: str
    expected_delivery_end_time: str
    CODE: ClassVar[str] = "120"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("expected_delivery_date_century", 32, 2, "text"),
        ("expected_delivery_date_year", 34, 2, "text"),
        ("expected_delivery_date_month", 36, 2, "text"),
        ("expected_delivery_date_day", 38, 2, "text"),
        ("expected_delivery_start_time", 40, 4, "text"),
        ("expected_delivery_end_time", 44, 4, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique130(Reflex52Record):
    preparation_year: str
    preparation_number: str
    appointment_date_century: str
    appointment_date_year: str
    appointment_date_month: str
    appointment_date_day: str
    appointment_start_time: str
    appointment_end_time: str
    CODE: ClassVar[str] = "130"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("appointment_date_century", 32, 2, "text"),
        ("appointment_date_year", 34, 2, "text"),
        ("appointment_date_month", 36, 2, "text"),
        ("appointment_date_day", 38, 2, "text"),
        ("appointment_start_time", 40, 4, "text"),
        ("appointment_end_time", 44, 4, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique140(Reflex52Record):
    preparation_year: str
    preparation_number: str
    quantity_level_1: int | None
    quantity_level_2: int | None
    quantity_level_3: int | None
    quantity_base_vl: int | None
    general_quantity_level_1: int | None
    general_quantity_level_2: int | None
    total_net_weight: Decimal | None
    total_gross_weight: Decimal | None
    total_volume: Decimal | None
    CODE: ClassVar[str] = "140"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("quantity_level_1", 32, 9, "int"),
        ("quantity_level_2", 41, 9, "int"),
        ("quantity_level_3", 50, 9, "int"),
        ("quantity_base_vl", 59, 9, "int"),
        ("general_quantity_level_1", 68, 9, "int"),
        ("general_quantity_level_2", 77, 9, "int"),
        ("total_net_weight", 86, 11, "decimal"),
        ("total_gross_weight", 97, 11, "decimal"),
        ("total_volume", 108, 11, "decimal"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique150(Reflex52Record):
    preparation_year: str
    preparation_number: str
    validated_quantity_level_1: int | None
    validated_quantity_level_2: int | None
    validated_quantity_level_3: int | None
    validated_quantity_base_vl: int | None
    validated_general_quantity_level_1: int | None
    validated_general_quantity_level_2: int | None
    validated_total_net_weight: Decimal | None
    validated_total_gross_weight: Decimal | None
    validated_total_volume: Decimal | None
    CODE: ClassVar[str] = "150"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("validated_quantity_level_1", 32, 9, "int"),
        ("validated_quantity_level_2", 41, 9, "int"),
        ("validated_quantity_level_3", 50, 9, "int"),
        ("validated_quantity_base_vl", 59, 9, "int"),
        ("validated_general_quantity_level_1", 68, 9, "int"),
        ("validated_general_quantity_level_2", 77, 9, "int"),
        ("validated_total_net_weight", 86, 11, "decimal"),
        ("validated_total_gross_weight", 97, 11, "decimal"),
        ("validated_total_volume", 108, 11, "decimal"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique160(Reflex52Record):
    preparation_year: str
    preparation_number: str
    stock_exit_date_century: str
    stock_exit_date_year: str
    stock_exit_date_month: str
    stock_exit_date_day: str
    stock_exit_time: str
    CODE: ClassVar[str] = "160"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("stock_exit_date_century", 32, 2, "text"),
        ("stock_exit_date_year", 34, 2, "text"),
        ("stock_exit_date_month", 36, 2, "text"),
        ("stock_exit_date_day", 38, 2, "text"),
        ("stock_exit_time", 40, 6, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique165(Reflex52Record):
    preparation_year: str
    preparation_number: str
    loading_date_century: str
    loading_date_year: str
    loading_date_month: str
    loading_date_day: str
    loading_code: str
    transport_means_type: str
    carrier_code: str
    carrier_loading_reference: str
    driver_name: str
    vehicle_registration: str
    carrier_appointment_taken: str
    carrier_appointment_date_century: str
    carrier_appointment_date_year: str
    carrier_appointment_date_month: str
    carrier_appointment_date_day: str
    carrier_appointment_time: str
    carrier_arrival_date_century: str
    carrier_arrival_date_year: str
    carrier_arrival_date_month: str
    carrier_arrival_date_day: str
    carrier_arrival_time: str
    carrier_departure_date_century: str
    carrier_departure_date_year: str
    carrier_departure_date_month: str
    carrier_departure_date_day: str
    carrier_departure_time: str
    transport_summary_number: str
    other_transport_document_reference: str
    shipment_number: str
    CODE: ClassVar[str] = "165"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("loading_date_century", 32, 2, "text"),
        ("loading_date_year", 34, 2, "text"),
        ("loading_date_month", 36, 2, "text"),
        ("loading_date_day", 38, 2, "text"),
        ("loading_code", 40, 6, "text"),
        ("transport_means_type", 46, 6, "text"),
        ("carrier_code", 52, 13, "text"),
        ("carrier_loading_reference", 65, 20, "text"),
        ("driver_name", 85, 20, "text"),
        ("vehicle_registration", 105, 10, "text"),
        ("carrier_appointment_taken", 115, 1, "text"),
        ("carrier_appointment_date_century", 116, 2, "text"),
        ("carrier_appointment_date_year", 118, 2, "text"),
        ("carrier_appointment_date_month", 120, 2, "text"),
        ("carrier_appointment_date_day", 122, 2, "text"),
        ("carrier_appointment_time", 124, 6, "text"),
        ("carrier_arrival_date_century", 130, 2, "text"),
        ("carrier_arrival_date_year", 132, 2, "text"),
        ("carrier_arrival_date_month", 134, 2, "text"),
        ("carrier_arrival_date_day", 136, 2, "text"),
        ("carrier_arrival_time", 138, 6, "text"),
        ("carrier_departure_date_century", 144, 2, "text"),
        ("carrier_departure_date_year", 146, 2, "text"),
        ("carrier_departure_date_month", 148, 2, "text"),
        ("carrier_departure_date_day", 150, 2, "text"),
        ("carrier_departure_time", 152, 6, "text"),
        ("transport_summary_number", 158, 9, "text"),
        ("other_transport_document_reference", 167, 20, "text"),
        ("shipment_number", 187, 11, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique199(Reflex52Record):
    preparation_year: str
    preparation_number: str
    comment: str
    comment_family: str
    CODE: ClassVar[str] = "199"
    FIELDS: ClassVar[tuple] = (
        ("preparation_year", 21, 2, "text"),
        ("preparation_number", 23, 9, "text"),
        ("comment", 32, 70, "text"),
        ("comment_family", 102, 3, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique210(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    order_physical_location: str
    order_year: str
    order_number: str
    order_line_number: str
    article_code: str
    article_logistics_variant_code: str
    owner_code: str
    quality_code: str
    final_recipient_code: str
    long_owner_code: str
    ordering_party_reference: str
    ordering_party_reference_line_number: str
    recipient_article_reference: str
    kit_code: str
    CODE: ClassVar[str] = "210"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("order_physical_location", 47, 3, "text"),
        ("order_year", 50, 2, "text"),
        ("order_number", 52, 9, "text"),
        ("order_line_number", 61, 7, "text"),
        ("article_code", 68, 16, "text"),
        ("article_logistics_variant_code", 84, 2, "text"),
        ("owner_code", 86, 3, "text"),
        ("quality_code", 89, 3, "text"),
        ("final_recipient_code", 92, 13, "text"),
        ("long_owner_code", 105, 13, "text"),
        ("ordering_party_reference", 118, 20, "text"),
        ("ordering_party_reference_line_number", 138, 7, "text"),
        ("recipient_article_reference", 145, 20, "text"),
        ("kit_code", 165, 1, "kit"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique220(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    odp_quantity_base_vl: int | None
    odp_net_weight: Decimal | None
    line_quantity_base_vl: int | None
    line_net_weight: Decimal | None
    validated_line_quantity_base_vl: int | None
    validated_line_net_weight: Decimal | None
    generated_remainder_quantity_base_vl: int | None
    generated_remainder_net_weight: Decimal | None
    substituted_quantity_numerator: int | None
    substituted_quantity_denominator: int | None
    substituted_net_weight: Decimal | None
    CODE: ClassVar[str] = "220"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("odp_quantity_base_vl", 47, 7, "int"),
        ("odp_net_weight", 54, 9, "decimal"),
        ("line_quantity_base_vl", 63, 7, "int"),
        ("line_net_weight", 70, 9, "decimal"),
        ("validated_line_quantity_base_vl", 79, 7, "int"),
        ("validated_line_net_weight", 86, 9, "decimal"),
        ("generated_remainder_quantity_base_vl", 95, 7, "int"),
        ("generated_remainder_net_weight", 102, 9, "decimal"),
        ("substituted_quantity_numerator", 111, 7, "int"),
        ("substituted_quantity_denominator", 118, 7, "int"),
        ("substituted_net_weight", 125, 9, "decimal"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique230(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    forced_scheduling_minimum_days: int | None
    validation_date_century: str
    validation_date_year: str
    validation_date_month: str
    validation_date_day: str
    validation_time: str
    CODE: ClassVar[str] = "230"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("forced_scheduling_minimum_days", 47, 3, "int"),
        ("validation_date_century", 50, 2, "text"),
        ("validation_date_year", 52, 2, "text"),
        ("validation_date_month", 54, 2, "text"),
        ("validation_date_day", 56, 2, "text"),
        ("validation_time", 58, 6, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique240(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    remainder_activity: str
    remainder_physical_location: str
    remainder_line_preparation_year: str
    remainder_line_number: str
    CODE: ClassVar[str] = "240"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("remainder_activity", 47, 3, "text"),
        ("remainder_physical_location", 50, 3, "text"),
        ("remainder_line_preparation_year", 53, 2, "text"),
        ("remainder_line_number", 55, 13, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique250(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    quantity_base_vl: int | None
    net_weight: Decimal | None
    supplier_code: str
    support_number: str
    parcel_number: str
    price: Decimal | None
    lot_1: str
    manufacturing_date_century: str
    manufacturing_date_year: str
    manufacturing_date_month: str
    manufacturing_date_day: str
    receipt_date_century: str
    receipt_date_year: str
    receipt_date_month: str
    receipt_date_day: str
    best_before_date_century: str
    best_before_date_year: str
    best_before_date_month: str
    best_before_date_day: str
    sell_by_date_century: str
    sell_by_date_year: str
    sell_by_date_month: str
    sell_by_date_day: str
    use_by_date_century: str
    use_by_date_year: str
    use_by_date_month: str
    use_by_date_day: str
    lot_2: str
    lot_3: str
    support_type_code: str
    parcel_type_code: str
    CODE: ClassVar[str] = "250"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("quantity_base_vl", 47, 7, "int"),
        ("net_weight", 54, 9, "decimal"),
        ("supplier_code", 63, 13, "text"),
        ("support_number", 76, 18, "text"),
        ("parcel_number", 94, 18, "text"),
        ("price", 112, 11, "decimal"),
        ("lot_1", 123, 20, "text"),
        ("manufacturing_date_century", 143, 2, "text"),
        ("manufacturing_date_year", 145, 2, "text"),
        ("manufacturing_date_month", 147, 2, "text"),
        ("manufacturing_date_day", 149, 2, "text"),
        ("receipt_date_century", 151, 2, "text"),
        ("receipt_date_year", 153, 2, "text"),
        ("receipt_date_month", 155, 2, "text"),
        ("receipt_date_day", 157, 2, "text"),
        ("best_before_date_century", 159, 2, "text"),
        ("best_before_date_year", 161, 2, "text"),
        ("best_before_date_month", 163, 2, "text"),
        ("best_before_date_day", 165, 2, "text"),
        ("sell_by_date_century", 167, 2, "text"),
        ("sell_by_date_year", 169, 2, "text"),
        ("sell_by_date_month", 171, 2, "text"),
        ("sell_by_date_day", 173, 2, "text"),
        ("use_by_date_century", 175, 2, "text"),
        ("use_by_date_year", 177, 2, "text"),
        ("use_by_date_month", 179, 2, "text"),
        ("use_by_date_day", 181, 2, "text"),
        ("lot_2", 183, 20, "text"),
        ("lot_3", 203, 20, "text"),
        ("support_type_code", 223, 3, "text"),
        ("parcel_type_code", 226, 3, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique251(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    blocked_specific_reason_flag: str
    blocking_reason_code: str
    blocked_customs_flag: str
    customs_release_date_century: str
    customs_release_date_year: str
    customs_release_date_month: str
    customs_release_date_day: str
    customs_reserved: str
    blocked_stabilization_flag: str
    stabilization_release_date_century: str
    stabilization_release_date_year: str
    stabilization_release_date_month: str
    stabilization_release_date_day: str
    stabilization_reserved: str
    blocked_control_flag: str
    blocked_reconditioning_flag: str
    reservation_recipient_code: str
    reservation_recipient_family_code: str
    reservation_reference: str
    allocation_ordering_party_code: str
    allocation_order_reference: str
    already_prepared_flag: str
    CODE: ClassVar[str] = "251"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("blocked_specific_reason_flag", 47, 1, "text"),
        ("blocking_reason_code", 48, 3, "text"),
        ("blocked_customs_flag", 51, 1, "text"),
        ("customs_release_date_century", 52, 2, "text"),
        ("customs_release_date_year", 54, 2, "text"),
        ("customs_release_date_month", 56, 2, "text"),
        ("customs_release_date_day", 58, 2, "text"),
        ("customs_reserved", 60, 4, "text"),
        ("blocked_stabilization_flag", 64, 1, "text"),
        ("stabilization_release_date_century", 65, 2, "text"),
        ("stabilization_release_date_year", 67, 2, "text"),
        ("stabilization_release_date_month", 69, 2, "text"),
        ("stabilization_release_date_day", 71, 2, "text"),
        ("stabilization_reserved", 73, 4, "text"),
        ("blocked_control_flag", 77, 1, "text"),
        ("blocked_reconditioning_flag", 78, 1, "text"),
        ("reservation_recipient_code", 79, 13, "text"),
        ("reservation_recipient_family_code", 92, 15, "text"),
        ("reservation_reference", 107, 20, "text"),
        ("allocation_ordering_party_code", 127, 13, "text"),
        ("allocation_order_reference", 140, 20, "text"),
        ("already_prepared_flag", 160, 1, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique260(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    start_serial_number: str
    end_serial_number: str
    entered_unit_count: int | None
    CODE: ClassVar[str] = "260"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("start_serial_number", 47, 30, "text"),
        ("end_serial_number", 77, 30, "text"),
        ("entered_unit_count", 107, 5, "int"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


@dataclass(kw_only=True)
class Reflex52Rubrique299(Reflex52Record):
    line_preparation_year: str
    line_number: str
    preparation_year: str
    preparation_number: str
    comment: str
    comment_family: str
    CODE: ClassVar[str] = "299"
    FIELDS: ClassVar[tuple] = (
        ("line_preparation_year", 21, 2, "text"),
        ("line_number", 23, 13, "text"),
        ("preparation_year", 36, 2, "text"),
        ("preparation_number", 38, 9, "text"),
        ("comment", 47, 70, "text"),
        ("comment_family", 117, 3, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls(**_values(payload, cls, values))


_PARSERS = {
    cls.CODE: cls
    for cls in (
        Reflex52Rubrique010,
        Reflex52Rubrique110,
        Reflex52Rubrique120,
        Reflex52Rubrique130,
        Reflex52Rubrique140,
        Reflex52Rubrique150,
        Reflex52Rubrique160,
        Reflex52Rubrique165,
        Reflex52Rubrique199,
        Reflex52Rubrique210,
        Reflex52Rubrique220,
        Reflex52Rubrique230,
        Reflex52Rubrique240,
        Reflex52Rubrique250,
        Reflex52Rubrique251,
        Reflex52Rubrique260,
        Reflex52Rubrique299,
    )
}


def parse_record(record: str) -> Reflex52Record:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    if rubrique is None:
        return Reflex52UnknownRecord()
    return _PARSERS[rubrique](**_values(payload, _PARSERS[rubrique], values))
