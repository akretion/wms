"""Pure fixed-width parser for Reflex Interface 52 preparation records."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Self

_SUPPORTED = ("150", "160", "165", "199", "210", "220")
_MINIMUM_LENGTHS = {
    "150": 118,
    "160": 45,
    "165": 197,
    "199": 104,
    "210": 165,
    "220": 133,
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
    if "\r" in payload or "\n" in payload or len(payload) < 14 or len(payload) > 270:
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
    if len(raw) != width:
        raise _error(rubrique, field, offset, raw, "wrong field width")
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
        raise _error(rubrique, "rubrique", 12, rubrique, "unsupported rubrique")
    minimum = _MINIMUM_LENGTHS[rubrique]
    if len(payload) < minimum:
        raise _error(
            rubrique, "record", 1, payload, f"expected at least {minimum} characters"
        )
    return rubrique, {
        "sequence": int(sequence),
        "application": application,
        "interface": interface,
        "rubrique": rubrique,
        "activity": _text(payload, 15, 3, rubrique, "activity"),
        "physical_location": _text(payload, 18, 3, rubrique, "physical_location"),
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
            if values[name] not in {"", "K", "C"}:
                raise _error(cls.CODE, name, offset, raw, "expected 'K', 'C', or blank")
        else:
            values[name] = raw.rstrip(" ")
    values["extension_data"] = payload[_MINIMUM_LENGTHS[cls.CODE] :].rstrip(" ")
    return values


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


_PARSERS = {
    cls.CODE: cls
    for cls in (
        Reflex52Rubrique150,
        Reflex52Rubrique160,
        Reflex52Rubrique165,
        Reflex52Rubrique199,
        Reflex52Rubrique210,
        Reflex52Rubrique220,
    )
}


def parse_record(record: str) -> Reflex52Record:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    return _PARSERS[rubrique](**_values(payload, _PARSERS[rubrique], values))
