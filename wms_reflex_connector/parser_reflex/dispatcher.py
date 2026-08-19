"""Unified, allowlisted dispatcher for supported Reflex interface records."""

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType
from typing import Any

from .gei62 import Reflex62Record
from .gei62 import parse_record as parse_62_record
from .prep52 import Reflex52Record
from .prep52 import parse_record as parse_52_record
from .rec53 import Reflex53Record
from .rec53 import parse_record as parse_53_record
from .stock55 import Reflex55Record
from .stock55 import parse_record as parse_55_record

ReflexRecord = Reflex52Record | Reflex53Record | Reflex55Record | Reflex62Record
ReflexRecordParser = Callable[[str], ReflexRecord]

INTERFACE_PARSERS: Mapping[str, ReflexRecordParser] = MappingProxyType(
    {
        "52": parse_52_record,
        "53": parse_53_record,
        "55": parse_55_record,
        "62": parse_62_record,
    }
)


class ReflexDispatchError(ValueError):
    """A record rejected before a concrete Reflex interface parser is selected."""

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


def _error(field: str, offset: int, value: str, reason: str) -> ReflexDispatchError:
    return ReflexDispatchError(
        f"Reflex dispatch {field} at offset {offset}: {reason} ({value!r})",
        rubrique=None,
        field=field,
        offset=offset,
        value=value,
    )


def _normalise_for_dispatch(record: Any) -> str:
    if not isinstance(record, str):
        raise _error("record", 1, repr(record), "record must be text")
    payload = (
        record[:-2]
        if record.endswith("\r\n")
        else record[:-1]
        if record.endswith("\n")
        else record
    )
    if "\r" in payload or "\n" in payload:
        raise _error("record", 1, record, "unexpected line terminator")
    if len(payload) < 11:
        raise _error("record", 1, record, "record is shorter than the common header")
    return payload


class ReflexInterfaceDispatcher:
    """Parse only the explicitly allowed interfaces from the fixed registry."""

    def __init__(self, allowed_interfaces: Iterable[str]) -> None:
        allowed = frozenset(allowed_interfaces)
        for interface in allowed:
            if not isinstance(interface, str) or interface not in INTERFACE_PARSERS:
                raise _error(
                    "allowed_interfaces",
                    0,
                    repr(interface),
                    "unsupported interface code",
                )
        self.allowed_interfaces = allowed

    def parse(self, record: str) -> ReflexRecord:
        payload = _normalise_for_dispatch(record)
        application = payload[7:9]
        if application != "HL":
            raise _error("application", 8, application, "expected 'HL'")
        interface = payload[9:11]
        parser = INTERFACE_PARSERS.get(interface)
        if parser is None:
            raise _error("interface", 10, interface, "unregistered interface")
        if interface not in self.allowed_interfaces:
            raise _error("interface", 10, interface, "interface is not allowed")
        return parser(record)
