# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import base64
import inspect
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from os import linesep
from typing import Any

from odoo import models
from odoo.exceptions import ValidationError


class ReflexLineDefinitionType(Enum):
    BASE = 0
    CONDITIONAL = 1
    RECORDSET = 2


@dataclass
class ReflexLineDefinition:
    line_class: type
    def_type: ReflexLineDefinitionType = ReflexLineDefinitionType.BASE
    should_produce_line_method_name: str = None
    recordset: str = None
    params: Any = None


class ReflexExportableMixin(models.AbstractModel):
    _name = "reflex.exportable.mixin"
    _description = "Reflex Exportable Mixin"  # TODO

    def _get_reflexline_definition(self):
        raise NotImplementedError()

    def get_source_module(self):
        raise NotImplementedError()

    def _prepare_export_data(self, idx):
        reflex_definitions = self._get_reflexline_definition()

        reflex_lines = []

        for definition in reflex_definitions:
            should_export_product = self._should_export_product()
            if not should_export_product:
                continue

            reflex_line_data_cls = self._get_data_class_from_def(definition)

            should_produce_line = self._should_produce_line(definition)

            if should_produce_line:
                reflex_line = self._instantiate_line(
                    definition, reflex_line_data_cls, idx
                )
                reflex_lines += reflex_line

        return [line.render() for line in reflex_lines]

    def _should_produce_line(self, definition: ReflexLineDefinition):
        if definition.should_produce_line_method_name:
            if not hasattr(self, definition.should_produce_line_method_name):
                raise ValidationError(
                    f"wms.product.sync does not have a {definition.should_produce_line_method_name} method"
                )
            return getattr(self, definition.should_produce_line_method_name)()
        return True

    def _instantiate_line(
        self, definition: ReflexLineDefinition, reflex_line_data_cls, idx
    ):
        if definition.def_type == ReflexLineDefinitionType.RECORDSET:
            return self._instantiate_line_from_recordset(
                definition, reflex_line_data_cls
            )
        else:
            line_class = definition.line_class
            data = reflex_line_data_cls.create(self, idx, definition.params, self.env)
            line = line_class(data)
            return [line]

    def _instantiate_line_from_recordset(self, definition, reflex_line_data_cls):
        recordset = definition.recordset
        lines = []
        for rec in recordset:
            line_class = definition.line_class
            data = reflex_line_data_cls.create(self, rec, definition.params, self.env)
            lines.append(line_class(data))
        return lines

    def _get_data_class_from_def(self, definition: ReflexLineDefinition):
        line_class = definition.line_class
        source_module = self.get_source_module()
        source_modules_classes = [
            (name, cls)
            for name, cls in inspect.getmembers(source_module, inspect.isclass)
            if cls.__module__ == source_module.__name__
        ]
        for name, member in source_modules_classes:
            if (
                inspect.isclass(member)
                and line_class.__name__ in name
                and "Data" in name
            ):
                return member

    def _format_to_exportfile(self, data):
        return self._format_to_exportfile_txt(data)

    def _format_to_exportfile_txt(self, data):
        txt_file = StringIO()
        for row in data:
            txt_file.write(row)
            txt_file.write(linesep)
        txt_file.seek(0)
        # TODO cleanup this code
        task = self._get_wms_export_task()
        return {
            "name": self._get_export_name(),
            "datas": base64.b64encode(txt_file.getvalue().encode("utf-8")),
            "task_id": task.id,
            "file_type": task.file_type,
        }
