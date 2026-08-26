# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.wms_connector.models.stock_move import StockMove
from odoo.addons.wms_reflex_connector.parser_reflex.dispatcher import (
    ReflexInterfaceDispatcher,
)

_logger = logging.getLogger(__name__)


class DataError(Exception):
    """Data Error"""


class ProcessorPickingBase(models.AbstractModel):
    _name = "processor.picking.base"
    _description = "Processor Picking Base"

    @property
    def warehouse_id(self):
        return self._context["warehouse"]

    @property
    def attachment_queue_id(self):
        return self._context["attachment_queue"]

    def _get_picking_type(self):
        raise NotImplementedError

    def _build_error_message(self, errors, todo):
        if todo:
            errors.append("\n ==== Lignes valides: ====")
            for move, qty in todo:
                errors.append(
                    "%s x %s (cmd: %s)"
                    % (qty, move.product_id.display_name, move.picking_id.origin)
                )
        return "\n".join(errors)

    def _process_lines(self, lines):
        raise NotImplementedError()

    def _process_move(self, move, state):
        if (
            len(move.move_line_ids) > 1
            and sum(move.move_line_ids.mapped("qty_done")) == 0
        ):
            # Setting the done qty on the move when having several
            # stock.move.line is not possible if this lines are empty
            # we just drop them before
            move.move_line_ids.unlink()
        move_qty = min(move.product_qty - move.quantity, state["qty"])
        move.quantity += move_qty
        state["qty"] -= move_qty
        return state, move, self.env["stock.move.line"]

    def _process_move_list(self, move_list, state, errors, done, **kwargs):
        pickings = self.env["stock.picking"]
        moves = self.env["stock.move"]
        move_lines = self.env["stock.move.line"]

        for move in move_list:
            state, new_moves, new_move_lines = self._process_move(move, state)
            moves |= new_moves
            move_lines |= new_move_lines
            pickings |= move.picking_id

        return (state, moves, move_lines, pickings)

    def _setup_state(self, state):
        return {"initial_qty": state["qty"], "qty": state["qty"]}

    def _post_process_parse_result_item(
        self, state, moves, move_lines, errors, done, allow_extra_qty, **kwargs
    ):
        initial_qty = state["initial_qty"]
        qty = state["qty"]
        move = moves[-1]
        if allow_extra_qty:
            # If will still have qty, this mean we have received more product
            # then expected, we just add them on the last move
            move.quantity_done += qty
            done.append((moves, initial_qty))
        else:
            errors.append(
                f"{initial_qty} x {move.product_id.reflex_code} -  "
                + f"{move.reflex_reference} : "
                + f"{qty} produits ont été expédiés en trop"
            )

    def _process_parse_result_item(
        self,
        item,
        errors,
        done,
        allow_extra_qty,
        **kwargs,
    ):
        state = self._setup_state(item)
        pickings = self.env["stock.picking"]
        moves = self.env["stock.move"]
        move_lines = self.env["stock.move.line"]

        for moves in item["move_ids"]:
            state, new_moves, new_move_lines, new_pickings = self._process_move_list(
                moves, state, errors, done, **kwargs
            )
            moves |= new_moves
            move_lines |= new_move_lines
            pickings |= new_pickings

        self._post_process_parse_result_item(
            state, moves, move_lines, errors, done, allow_extra_qty, **kwargs
        )

        return pickings, moves, move_lines

    def _post_process_pickings_move_move_line(self, pickings, moves, move_lines):
        pickings.with_context(validation_from_sync=True).button_validate()
        pickings.wms_import_attachment_id = self.attachment_queue_id.id

    def _pre_process_parse_result(self, moves_todo):
        return moves_todo

    def _process_parse_result_list(self, parse_result, allow_extra_qty, **kwargs):
        errors = []
        done = []
        pickings = self.env["stock.picking"]
        moves = self.env["stock.move"]
        move_lines = self.env["stock.move.line"]
        for item in parse_result:
            new_pickings, new_moves, new_move_lines = self._process_parse_result_item(
                item,
                errors,
                done,
                allow_extra_qty,
                **kwargs,
            )
            moves |= new_moves
            move_lines |= new_move_lines
            pickings |= new_pickings
        if errors:
            raise UserError(self._build_error_message(errors, done))
        return pickings, moves, move_lines

    def _process_parse_result(
        self,
        parse_result,
        allow_extra_qty=False,
        **kwargs,
    ):
        pickings = self.env["stock.picking"]
        parse_result = self._pre_process_parse_result(parse_result, **kwargs)
        pickings, moves, move_lines = self._process_parse_result_list(
            parse_result, allow_extra_qty, **kwargs
        )
        self._post_process_pickings_move_move_line(
            pickings, moves, move_lines, **kwargs
        )


class ProcessorPickingIn(models.TransientModel):
    _inherit = "processor.picking.base"
    _name = "processor.picking.in"
    _description = "Processor Picking In"

    def _get_interface_list(self):
        raise NotImplementedError()

    def _get_picking_type(self):
        return self.warehouse_id.in_type_id

    def _process_line(self, line_data, state, moves):
        raise NotImplementedError()

    def run(self, string_buffer):
        dispatcher = ReflexInterfaceDispatcher(self._get_interface_list())
        state = {}
        moves = []
        for line in iter(string_buffer.readline, ""):
            line_data = dispatcher.parse(line)
            new_state = self._process_line(line_data, state, moves)
            state.update(new_state)
        self._process_parse_result(moves, allow_extra_qty=True)
        # TODO(franz): bring warnings back in
        # self.attachment_queue_id.description = "\n".join(warnings)


class ProcessorPickingOut(models.TransientModel):
    _inherit = "processor.picking.base"
    _name = "processor.picking.out"
    _description = "Processor Picking Out"

    def _get_interface_list(self):
        raise NotImplementedError()

    def _get_picking_type(self):
        return self.warehouse_id.in_type_id

    def _process_line(self, line_data, state, moves):
        raise NotImplementedError()

    def run(self, string_buffer):
        dispatcher = ReflexInterfaceDispatcher(self._get_interface_list())
        state = {}
        moves = []
        for line in iter(string_buffer.readline, ""):
            line_data = dispatcher.parse(line)
            self._process_line(line_data, state, moves)
        self._process_parse_result(moves, allow_extra_qty=True)
        # TODO(franz): bring warnings back in
        # self.attachment_queue_id.description = "\n".join(warnings)
