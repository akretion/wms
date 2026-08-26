"""Pure fixed-width parser for Reflex Interface 53 reception records."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Self

_SUPPORTED = ("110", "120", "130", "150", "310", "340")


class Reflex53ParseError(ValueError):
    """A malformed Interface 53 record, with protocol location context."""

    def __init__(
        self,
        message: str,
        *,
        rubrique: str | None,
        field: str,
        offset: int,
        value: str,
    ) -> None:
        super().__init__(message)
        self.rubrique = rubrique
        self.field = field
        self.offset = offset
        self.value = value


def _error(
    rubrique: str | None, field: str, offset: int, value: str, reason: str
) -> Reflex53ParseError:
    return Reflex53ParseError(
        f"Interface 53{rubrique} {field} at offset {offset}: {reason} ({value!r})",
        rubrique=rubrique,
        field=field,
        offset=offset,
        value=value,
    )


def _normalise_payload(record: str) -> str:
    """Remove exactly one permitted line terminator and validate record size."""
    if not isinstance(record, str):
        raise _error(None, "record", 1, repr(record), "record must be text")
    payload = record
    if payload.endswith("\r\n"):
        payload = payload[:-2]
    elif payload.endswith("\n"):
        payload = payload[:-1]
    if "\r" in payload or "\n" in payload:
        raise _error(None, "record", 1, record, "unexpected line terminator")
    return payload


def _field(
    payload: str, offset: int, width: int, rubrique: str | None, field: str
) -> str:
    """Return an exact one-based payload slice."""
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
    envelope_rubrique = payload[11:14]
    sequence_raw = _field(payload, 1, 7, envelope_rubrique, "sequence")
    if not sequence_raw.isascii() or not sequence_raw.isdigit():
        raise _error(
            envelope_rubrique, "sequence", 1, sequence_raw, "expected ASCII digits"
        )
    application = _field(payload, 8, 2, envelope_rubrique, "application")
    if application != "HL":
        raise _error(envelope_rubrique, "application", 8, application, "expected 'HL'")
    interface = _field(payload, 10, 2, envelope_rubrique, "interface")
    if interface != "53":
        raise _error(envelope_rubrique, "interface", 10, interface, "expected '53'")
    rubrique = _field(payload, 12, 3, envelope_rubrique, "rubrique")
    if rubrique not in _SUPPORTED:
        return None, None
    common = {
        "sequence": int(sequence_raw),
        "application": application,
        "interface": interface,
        "rubrique": rubrique,
        "activity": _text(payload, 15, 3, rubrique, "activity"),
        "physical_location": _text(payload, 18, 3, rubrique, "physical_location"),
        "reception_year": _text(payload, 21, 2, rubrique, "reception_year"),
        "reception_number": _text(payload, 23, 9, rubrique, "reception_number"),
    }
    return rubrique, common


def _prepare(record: str, expected: str) -> tuple[str, dict[str, Any]]:
    payload = _normalise_payload(record)
    rubrique, common = _envelope(payload)
    if rubrique != expected:
        raise _error(rubrique, "rubrique", 12, rubrique, f"expected '{expected}'")
    return payload, common


@dataclass(kw_only=True)
class Reflex53UnknownRecord:
    CODE: ClassVar[str] = None


@dataclass(kw_only=True)
class Reflex53Record:
    sequence: int
    application: str
    interface: str
    rubrique: str
    activity: str
    physical_location: str
    reception_year: str
    reception_number: str


@dataclass(kw_only=True)
class Reflex53Rubrique110(Reflex53Record):
    entry_date_century: str
    entry_date_year: str
    entry_date_month: str
    entry_date_day: str
    entry_time: str
    reception_reason: str
    CODE: ClassVar[str] = "110"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        values.update(
            entry_date_century=_text(payload, 32, 2, cls.CODE, "entry_date_century"),
            entry_date_year=_text(payload, 34, 2, cls.CODE, "entry_date_year"),
            entry_date_month=_text(payload, 36, 2, cls.CODE, "entry_date_month"),
            entry_date_day=_text(payload, 38, 2, cls.CODE, "entry_date_day"),
            entry_time=_text(payload, 40, 6, cls.CODE, "entry_time"),
            reception_reason=_text(payload, 46, 3, cls.CODE, "reception_reason"),
        )
        return cls(**values)


@dataclass(kw_only=True)
class Reflex53Rubrique120(Reflex53Record):
    ordering_party: str
    customs_delay: str
    workshop: str
    reception_type: str
    CODE: ClassVar[str] = "120"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        values.update(
            ordering_party=_text(payload, 32, 13, cls.CODE, "ordering_party"),
            customs_delay=_text(payload, 45, 3, cls.CODE, "customs_delay"),
            workshop=_text(payload, 48, 3, cls.CODE, "workshop"),
            reception_type=_text(payload, 51, 3, cls.CODE, "reception_type"),
        )
        return cls(**values)


@dataclass(kw_only=True)
class Reflex53Rubrique130(Reflex53Record):
    supplier: str
    reception_reference: str
    supplier_delivery_note: str
    CODE: ClassVar[str] = "130"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        values.update(
            supplier=_text(payload, 32, 13, cls.CODE, "supplier"),
            reception_reference=_text(payload, 45, 20, cls.CODE, "reception_reference"),
            supplier_delivery_note=_text(
                payload, 65, 10, cls.CODE, "supplier_delivery_note"
            ),
        )
        return cls(**values)


@dataclass(kw_only=True)
class Reflex53Rubrique150(Reflex53Record):
    carrier: str
    driver: str
    transport_document: str
    license_plate: str
    arrival_date_century: str
    arrival_date_year: str
    arrival_date_month: str
    arrival_date_day: str
    arrival_time: str
    appointment_date_century: str
    appointment_date_year: str
    appointment_date_month: str
    appointment_date_day: str
    appointment_start: str
    appointment_end: str
    confirmed_flag: str
    CODE: ClassVar[str] = "150"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        specs = (
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
        )
        values.update(
            {
                name: _text(payload, offset, width, cls.CODE, name)
                for name, offset, width in specs
            }
        )
        return cls(**values)


@dataclass(kw_only=True)
class Reflex53Rubrique310(Reflex53Record):
    reception_line: str
    article: str
    logistics_variant: str
    logistics_variant_order_reference: str
    supplier_packaging_reference: str
    owner: str
    quality: str
    CODE: ClassVar[str] = "310"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        specs = (
            ("reception_line", 32, 6),
            ("article", 38, 16),
            ("logistics_variant", 54, 2),
            ("logistics_variant_order_reference", 56, 16),
            ("supplier_packaging_reference", 72, 20),
            ("owner", 92, 3),
            ("quality", 95, 3),
        )
        values.update(
            {
                name: _text(payload, offset, width, cls.CODE, name)
                for name, offset, width in specs
            }
        )
        return cls(**values)


@dataclass(kw_only=True)
class Reflex53Rubrique340(Reflex53Record):
    reception_line: str
    quantity_level_1: int | None
    quantity_level_2: int | None
    quantity_level_3: int | None
    quantity_base_vl: int | None
    net_weight: Decimal | None
    gross_weight: Decimal | None
    volume: Decimal | None
    lot_1: str
    manufacturing_date_century: str
    manufacturing_date_year: str
    manufacturing_date_month: str
    manufacturing_date_day: str
    best_before_date: str
    sale_deadline_date: str
    consumption_deadline_date: str
    scheduling_date: str
    missing_flag: str
    missing_reason: str
    lot_2: str
    lot_3: str
    control_flag: str
    repackage_flag: str
    special_block_flag: str
    block_reason: str
    detail_owner: str
    detail_quality: str
    reservation_recipient: str
    reservation_recipient_family: str
    reservation_reference: str
    detail_reception_line_number: str
    CODE: ClassVar[str] = "340"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        values["reception_line"] = _text(payload, 32, 6, cls.CODE, "reception_line")
        int_specs = (
            ("quantity_level_1", 38),
            ("quantity_level_2", 45),
            ("quantity_level_3", 52),
            ("quantity_base_vl", 59),
        )
        values.update(
            {
                name: _optional_int(
                    _field(payload, offset, 7, cls.CODE, name), cls.CODE, name, offset
                )
                for name, offset in int_specs
            }
        )
        decimal_specs = (("net_weight", 66), ("gross_weight", 75), ("volume", 84))
        values.update(
            {
                name: _optional_decimal_9_3(
                    _field(payload, offset, 9, cls.CODE, name), cls.CODE, name, offset
                )
                for name, offset in decimal_specs
            }
        )
        specs = (
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
        )
        values.update(
            {
                name: _text(payload, offset, width, cls.CODE, name)
                for name, offset, width in specs
            }
        )
        return cls(**values)


_PARSERS = {
    "110": Reflex53Rubrique110,
    "120": Reflex53Rubrique120,
    "130": Reflex53Rubrique130,
    "150": Reflex53Rubrique150,
    "310": Reflex53Rubrique310,
    "340": Reflex53Rubrique340,
}


def parse_record(record: str) -> Reflex53Record:
    payload = _normalise_payload(record)
    rubrique, common = _envelope(payload)
    if rubrique is None:
        return Reflex53UnknownRecord()
    return _PARSERS[rubrique]._parse_prepared(payload, common)
