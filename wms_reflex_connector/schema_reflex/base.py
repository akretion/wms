# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
from dataclasses import dataclass, fields
from typing import Any, dataclass_transform

from unidecode import unidecode

from odoo.api import Environment
from odoo.tools import float_compare


@dataclass_transform(kw_only_default=True)
class AutoDataclassMeta(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        type.__setattr__(cls, "_allow_dataclass", True)

        try:
            dataclass(cls, kw_only=True)
        finally:
            type.__setattr__(cls, "_allow_dataclass", False)

        return cls

    def __setattr__(cls, name: str, value: Any) -> None:
        dataclass_attributes = {
            "__dataclass_params__",
            "__dataclass_fields__",
        }

        allowed = cls.__dict__.get("_allow_dataclass", False)

        if name in dataclass_attributes and not allowed:
            raise TypeError(
                f"Do not apply @dataclass to {cls.__name__}; "
                "the metaclass applies it automatically"
            )

        super().__setattr__(name, value)


class ReflexLineDataBase(metaclass=AutoDataclassMeta):
    num_sequence: int
    code_activity: str
    code_application: str = "HL"
    env: Environment

    def __post_init__(self):
        self.convert_data()

    def convert_data(self):
        for field in fields(self):
            field_name = field.name
            convert_function_name = f"{field.name}_convert"
            if hasattr(self, convert_function_name):
                self[field_name] = self[convert_function_name](self[field_name])

    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError


class ReflexLine:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def _format_values(
        self,
        field_name,
        size,
        value="",
        empty_if_zero=False,
        decimal=2,
        truncate_silent=False,
    ):
        is_number = False
        if isinstance(value, datetime.datetime):
            fmt_val = datetime.date.strftime(value.date(), "%Y%m%d")
        elif isinstance(value, int):
            fmt_val = str(value)
            is_number = True
        elif isinstance(value, float):
            if float_compare(value, 0, 3) == 0 and empty_if_zero:
                fmt_val = ""
            else:
                fmt_val = str(int(value * 10**decimal))
                is_number = True
        elif isinstance(value, str):
            fmt_val = unidecode(value)
        else:
            raise ValueError("Unsupported value type")
        if len(fmt_val) > size:
            if truncate_silent:
                fmt_val = fmt_val[:size]
            else:
                raise ValueError(
                    "{}: {} trop long, taille maximale est de {}".format(
                        field_name, fmt_val, size
                    )
                )
        if is_number:
            return fmt_val.rjust(size, "0")
        else:
            return fmt_val.ljust(size, " ")

    def render(self):
        res = ""
        for fmt_data in self.get_values():
            field_name = fmt_data[0]
            size = fmt_data[1]
            value = fmt_data[2] if len(fmt_data) > 2 else ""
            options = fmt_data[3] if len(fmt_data) > 3 else {}
            res += self._format_values(field_name, size, value, **options)
        return res

    def get_values(self):
        raise NotImplementedError


class ReflexLinePicking(ReflexLine):
    def format_date(self, date):
        return [(2, date.year[:2]), (2, date.year[2:]), (2, date.month), (2, date.day)]
