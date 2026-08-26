"""Pure fixed-width parser for Reflex Interface 55 stock-detail records."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Self

_SUPPORTED = ("110",)


class Reflex55ParseError(ValueError):
    """A malformed Interface 55 record, with protocol location context."""

    def __init__(
        self, message: str, *, rubrique: str | None, field: str, offset: int, value: str
    ) -> None:
        super().__init__(message)
        self.rubrique, self.field, self.offset, self.value = (
            rubrique,
            field,
            offset,
            value,
        )


def _error(
    rubrique: str | None, field: str, offset: int, value: str, reason: str
) -> Reflex55ParseError:
    return Reflex55ParseError(
        f"Interface 55 {field} at offset {offset}: {reason} ({value!r})",
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
    if "\r" in payload or "\n" in payload:
        raise _error(None, "record", 1, record, "unexpected line terminator")
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


def _require_padding(payload: str, offset: int, width: int, rubrique: str) -> None:
    raw = _field(payload, offset, width, rubrique, "padding")
    if raw != " " * width:
        raise _error(rubrique, "padding", offset, raw, "expected spaces only")


def _envelope(payload: str) -> tuple[str, dict[str, Any]]:
    candidate = payload[11:14]
    sequence_raw = _field(payload, 1, 7, candidate, "sequence")
    if not sequence_raw.isascii() or not sequence_raw.isdigit():
        raise _error(candidate, "sequence", 1, sequence_raw, "expected ASCII digits")
    application = _field(payload, 8, 2, candidate, "application")
    if application != "HL":
        raise _error(candidate, "application", 8, application, "expected 'HL'")
    interface = _field(payload, 10, 2, candidate, "interface")
    if interface != "55":
        raise _error(candidate, "interface", 10, interface, "expected '55'")
    rubrique = _field(payload, 12, 3, candidate, "rubrique")
    if rubrique not in _SUPPORTED:
        return None, None
    return rubrique, {
        "sequence": int(sequence_raw),
        "application": application,
        "interface": interface,
        "rubrique": rubrique,
    }


def _prepare(record: str, expected: str) -> tuple[str, dict[str, Any]]:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    if rubrique != expected:
        raise _error(rubrique, "rubrique", 12, rubrique, f"expected '{expected}'")
    return payload, values


@dataclass(kw_only=True)
class Reflex55UnknownRecord:
    CODE: ClassVar[str] = None


@dataclass(kw_only=True)
class Reflex55Record:
    sequence: int
    application: str
    interface: str
    rubrique: str


@dataclass(kw_only=True)
class Reflex55Rubrique110(Reflex55Record):
    physical_depot_code: str
    stock_type_code: str
    activity_code: str
    article_code: str
    article_logistics_variant_code: str
    owner_code: str
    quality_code: str
    available_for_preparation_flag: str
    blocked_special_reason_flag: str
    blocking_reason_code: str
    blocked_customs_flag: str
    blocked_stabilization_flag: str
    blocked_control_flag: str
    blocked_reconditioning_flag: str
    blocked_exit_location_flag: str
    blocked_inventory_flag: str
    supplier_code: str
    lot_1: str
    scheduling_date_century: str
    scheduling_date_year: str
    scheduling_date_month: str
    scheduling_date_day: str
    manufacturing_date_century: str
    manufacturing_date_year: str
    manufacturing_date_month: str
    manufacturing_date_day: str
    reception_date_century: str
    reception_date_year: str
    reception_date_month: str
    reception_date_day: str
    sale_deadline_date_century: str
    sale_deadline_date_year: str
    sale_deadline_date_month: str
    sale_deadline_date_day: str
    consumption_deadline_date_century: str
    consumption_deadline_date_year: str
    consumption_deadline_date_month: str
    consumption_deadline_date_day: str
    best_before_date_century: str
    best_before_date_year: str
    best_before_date_month: str
    best_before_date_day: str
    quantity_base_vl: int | None
    net_weight: Decimal | None
    generation_date_century: str
    generation_date_year: str
    generation_date_month: str
    generation_date_day: str
    generation_time: str
    reservation_recipient_code: str
    reservation_recipient_family_code: str
    at_picking_flag: str
    lot_2: str
    lot_3: str
    odp_reservation_reference: str
    CODE: ClassVar[str] = "110"
    FIELDS: ClassVar[tuple[tuple[str, int, int, str], ...]] = (
        ("physical_depot_code", 15, 3, "text"),
        ("stock_type_code", 18, 3, "text"),
        ("activity_code", 21, 3, "text"),
        ("article_code", 24, 16, "text"),
        ("article_logistics_variant_code", 40, 2, "text"),
        ("owner_code", 42, 3, "text"),
        ("quality_code", 45, 3, "text"),
        ("available_for_preparation_flag", 48, 1, "text"),
        ("blocked_special_reason_flag", 49, 1, "text"),
        ("blocking_reason_code", 50, 3, "text"),
        ("blocked_customs_flag", 53, 1, "text"),
        ("blocked_stabilization_flag", 54, 1, "text"),
        ("blocked_control_flag", 55, 1, "text"),
        ("blocked_reconditioning_flag", 56, 1, "text"),
        ("blocked_exit_location_flag", 57, 1, "text"),
        ("blocked_inventory_flag", 58, 1, "text"),
        ("supplier_code", 59, 13, "text"),
        ("lot_1", 72, 20, "text"),
        ("scheduling_date_century", 92, 2, "text"),
        ("scheduling_date_year", 94, 2, "text"),
        ("scheduling_date_month", 96, 2, "text"),
        ("scheduling_date_day", 98, 2, "text"),
        ("manufacturing_date_century", 100, 2, "text"),
        ("manufacturing_date_year", 102, 2, "text"),
        ("manufacturing_date_month", 104, 2, "text"),
        ("manufacturing_date_day", 106, 2, "text"),
        ("reception_date_century", 108, 2, "text"),
        ("reception_date_year", 110, 2, "text"),
        ("reception_date_month", 112, 2, "text"),
        ("reception_date_day", 114, 2, "text"),
        ("sale_deadline_date_century", 116, 2, "text"),
        ("sale_deadline_date_year", 118, 2, "text"),
        ("sale_deadline_date_month", 120, 2, "text"),
        ("sale_deadline_date_day", 122, 2, "text"),
        ("consumption_deadline_date_century", 124, 2, "text"),
        ("consumption_deadline_date_year", 126, 2, "text"),
        ("consumption_deadline_date_month", 128, 2, "text"),
        ("consumption_deadline_date_day", 130, 2, "text"),
        ("best_before_date_century", 132, 2, "text"),
        ("best_before_date_year", 134, 2, "text"),
        ("best_before_date_month", 136, 2, "text"),
        ("best_before_date_day", 138, 2, "text"),
        ("quantity_base_vl", 140, 9, "int"),
        ("net_weight", 149, 9, "decimal"),
        ("generation_date_century", 158, 2, "text"),
        ("generation_date_year", 160, 2, "text"),
        ("generation_date_month", 162, 2, "text"),
        ("generation_date_day", 164, 2, "text"),
        ("generation_time", 166, 6, "text"),
        ("reservation_recipient_code", 172, 13, "text"),
        ("reservation_recipient_family_code", 185, 15, "text"),
        ("at_picking_flag", 200, 1, "text"),
        ("lot_2", 201, 20, "text"),
        ("lot_3", 221, 20, "text"),
        ("odp_reservation_reference", 241, 20, "text"),
    )

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        for name, offset, width, kind in cls.FIELDS:
            raw = _field(payload, offset, width, cls.CODE, name)
            values[name] = (
                _optional_int(raw, cls.CODE, name, offset)
                if kind == "int"
                else _optional_decimal_9_3(raw, cls.CODE, name, offset)
                if kind == "decimal"
                else raw.rstrip(" ")
            )
        _require_padding(payload, 261, 10, cls.CODE)
        return cls(**values)


_PARSERS = {"110": Reflex55Rubrique110}


def parse_record(record: str) -> Reflex55Record:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    if rubrique is None:
        return Reflex55UknownRecord()
    return _PARSERS[rubrique]._parse_prepared(payload, values)
