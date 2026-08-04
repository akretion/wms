"""Pure fixed-width parser for Reflex Interface 62 GEI movement records."""

from dataclasses import dataclass
from typing import Any, ClassVar, Self

_SUPPORTED = ("110", "112")


class Reflex62ParseError(ValueError):
    """A malformed Interface 62 record, with protocol location context."""

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
) -> Reflex62ParseError:
    return Reflex62ParseError(
        f"Interface 62 {field} at offset {offset}: {reason} ({value!r})",
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
    if len(payload) != 270:
        raise _error(None, "record", 1, record, "expected 270 characters")
    return payload


def _field(
    payload: str, offset: int, width: int, rubrique: str | None, field: str
) -> str:
    """Return an exact one-based payload slice."""
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


def _require_padding(
    payload: str, offset: int, width: int, rubrique: str, field: str = "padding"
) -> None:
    raw = _field(payload, offset, width, rubrique, field)
    if raw != " " * width:
        raise _error(rubrique, field, offset, raw, "expected spaces only")


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
    if interface != "62":
        raise _error(envelope_rubrique, "interface", 10, interface, "expected '62'")
    rubrique = _field(payload, 12, 3, envelope_rubrique, "rubrique")
    if rubrique not in _SUPPORTED:
        raise _error(rubrique, "rubrique", 12, rubrique, "unsupported rubrique")
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
class Reflex62Record:
    sequence: int
    application: str
    interface: str
    rubrique: str


@dataclass(kw_only=True)
class Reflex62Rubrique110(Reflex62Record):
    physical_location: str
    movement_year: str
    movement_number: str
    movement_direction: str
    stock_type: str
    gei_movement_type: str
    stock_movement_type: str
    stock_movement_reference: str
    miscellaneous_reason: str
    article: str
    quality: str
    movement_quantity_base_vl: int | None
    CODE: ClassVar[str] = "110"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        text_specs = (
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
        )
        values.update(
            {
                name: _text(payload, offset, width, cls.CODE, name)
                for name, offset, width in text_specs
            }
        )
        values["movement_quantity_base_vl"] = _optional_int(
            _field(payload, 170, 9, cls.CODE, "movement_quantity_base_vl"),
            cls.CODE,
            "movement_quantity_base_vl",
            170,
        )
        _require_padding(payload, 248, 23, cls.CODE)
        return cls(**values)


@dataclass(kw_only=True)
class Reflex62Rubrique112(Reflex62Record):
    creation_date: str
    CODE: ClassVar[str] = "112"

    @classmethod
    def parse(cls, record: str) -> Self:
        payload, values = _prepare(record, cls.CODE)
        return cls._parse_prepared(payload, values)

    @classmethod
    def _parse_prepared(cls, payload: str, values: dict[str, Any]) -> Self:
        creation_date = _field(payload, 176, 8, cls.CODE, "creation_date")
        if not creation_date.isascii() or not creation_date.isdigit():
            raise _error(
                cls.CODE,
                "creation_date",
                176,
                creation_date,
                "expected eight ASCII digits",
            )
        values["creation_date"] = creation_date
        _require_padding(payload, 210, 61, cls.CODE)
        return cls(**values)


_PARSERS = {
    "110": Reflex62Rubrique110,
    "112": Reflex62Rubrique112,
}


def parse_record(record: str) -> Reflex62Record:
    payload = _normalise_payload(record)
    rubrique, values = _envelope(payload)
    return _PARSERS[rubrique]._parse_prepared(payload, values)
