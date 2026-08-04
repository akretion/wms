import inspect
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..schema_reflex import art03
from ..schema_reflex.art03 import (
    ReflexLine03110,
    ReflexLine03110Data,
    ReflexLine03112,
    ReflexLine03112Data,
    ReflexLine03119,
    ReflexLine03119Data,
    ReflexLine03120,
    ReflexLine03120Data,
)


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


class WmsProductSync(models.Model):
    _inherit = "wms.product.sync"

    def get_source_module(self):
        raise NotImplementedError()

    def _get_data_class_from_def(self, definition: ReflexLineDefinition):
        line_class = definition.line_class
        source_module = self.get_source_module()
        source_modules_classes = [
            (name, cls)
            for name, cls in inspect.getmembers(source_module, inspect.isclass)
            if cls.__module__ == source_module.__name__
        ]
        for name, member in source_modules_classes:
            if inspect.isclass(member):
                if line_class.__name__ in name and "Data" in name:
                    return member

    # def test(self):
    #     self._get_data_class_from_line_class(ReflexLine03110)

    def _get_reflexline_definition(self):
        raise NotImplementedError()

    def _should_export_product(self):
        return True

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
                definition, reflex_line_data_cls, idx
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

    def _get_export_name(self):
        raise NotImplementedError()

    @property
    def record_per_file(self):
        return 1000

    # TODO FIXME
    def _format_to_exportfile_txt(self, data):
        vals = super()._format_to_exportfile_txt(data)
        vals["task_id"] = self.warehouse_id.wms_export_task_id.id
        return vals

    def track_export(self, attachment):
        super().track_export(attachment)
        if self._context.get("force_reflex_export"):
            attachment._run()
            vals = {
                "state": "done",
                "date_done": fields.Datetime.now(),
            }
            attachment.write(vals)
