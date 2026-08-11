# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import logging
from collections import Counter
from datetime import datetime

from odoo import models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.wms_reflex_connector.parser_reflex.rec53 import parse_record

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

    def _reset_picking(self, todo):
        # Ensure that we do not have qty done set on the picking
        # due to wrong manipulation
        reset_pickings = self.env["stock.picking"]
        for (
            moves,
            _qty,
        ) in todo:
            reset_pickings |= moves.picking_id
        for line in reset_pickings.move_lines:
            if line.quantity_done:
                line.quantity_done = 0

    def _process_lines(self, lines):
        raise NotImplementedError()

    def _process_todo(self, todo, allow_extra_qty=False, carrier_code=False):
        errors = []
        done = []
        pickings = self.env["stock.picking"]
        self._reset_picking(todo)
        for moves, qty in todo:
            initial_qty = qty
            for move in moves:
                # FIXME in V18
                if (
                    len(move.move_line_ids) > 1
                    and sum(move.move_line_ids.mapped("qty_done")) == 0
                ):
                    # Setting the done qty on the move when having several
                    # stock.move.line is not possible if this lines are empty
                    # we just drop them before
                    move.move_line_ids.unlink()
                move_qty = min(move.product_qty - move.quantity_done, qty)
                move.quantity_done += move_qty
                qty -= move_qty
                pickings |= move.picking_id
                if not qty:
                    continue
            if qty:
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
            else:
                done.append((moves, initial_qty))
        if errors:
            raise UserError(self._build_error_message(errors, done))
        # confirm and always do a backorder
        if carrier_code:
            carrier_id = self.env["delivery.carrier"].search(
                [("delivery_carrier_code_reflex", "=", carrier_code)]
            )
            pickings.carrier_id = carrier_id.id if carrier_id else False
        pickings.with_context(validation_from_sync=True).button_validate()
        pickings.wms_import_attachment_id = self.attachment_queue_id.id


class ProcessorPickingIn(models.TransientModel):
    _inherit = "processor.picking.base"
    _name = "processor.picking.in"
    _description = "Processor Picking In"

    def _get_picking_type(self):
        return self.warehouse_id.in_type_id

    def _get_move(self, order_ref, product_reflex_code, qty):
        raise NotImplementedError()
        # move = self.env["stock.move"].search(
        #     [
        #         "|",
        #         ("picking_id.origin", "=", order_ref),
        #         ("picking_id", "in", self._get_picking_name(order_ref).ids),
        #         ("product_id.reflex_code", "=", product_reflex_code),
        #         ("state", "not in", ("cancel", "done")),
        #     ]
        # )
        # if not move:
        #     raise DataError(
        #         f"{qty} x {product_reflex_code} (cmd: {order_ref}) : "
        #         + "Aucune ligne d'expédition trouvé"
        #     )
        # return move

    def run(self, string_buffer):
        errors = []
        warnings = []
        lines = []
        for line in iter(string_buffer.readline, ""):
            lines.push(parse_record(line))
        todo = self._process_lines(lines)
        self._process_todo(lines, allow_extra_qty=True)
        self.attachment_queue_id.description = "\n".join(warnings)


class ProcessorPickingOut(models.TransientModel):
    _inherit = "processor.picking.base"
    _name = "processor.picking.out"
    _description = "Processor Picking Out"

    def _get_picking_type(self):
        return self.warehouse_id.out_type_id

    def _get_move(self, reflex_move_ref, product_reflex_code, qty):
        if not reflex_move_ref:
            raise DataError("Pas de reference reflex pour cette expedition")

        if reflex_move_ref[-3:] == "BIS":
            # TODO see why we have this case and if happen often
            _logger.warning("Solve Aliné Hack, remove BIS from reference")
            reflex_move_ref = reflex_move_ref[:-3].strip()

        moves = self.env["stock.move"].search(
            [
                ("reflex_reference", "=", reflex_move_ref),
                ("product_id.reflex_code", "=", product_reflex_code),
                ("state", "not in", ("cancel", "done")),
            ]
        )

        # Migration hack
        if not moves and reflex_move_ref[0:2] == "ZM":
            sale = self.env["sale.order"].search([("name", "=", reflex_move_ref[:-2])])
            if sale:
                picking = sale.picking_ids.filtered(
                    lambda s: s.state != "cancel"
                ).sorted("id")
                if picking:
                    reflex_move_ref = picking[0].name + reflex_move_ref[-2:]
                    moves = self._get_move(reflex_move_ref, product_reflex_code, qty)

        if not moves:
            raise DataError(
                f"{qty} x {product_reflex_code} -  "
                + f"{reflex_move_ref} : aucune ligne d'expédition trouvé"
            )
        return moves

    def run(self, string_buffer):
        errors = []
        warnings = []
        todo = []
        carrier_code = ""
        for line in iter(string_buffer.readline, ""):
            try:
                if "HL52210" in line:
                    reflex_move_ref = line[117:137].strip()
                    product_reflex_code = line[67:83].strip()
                elif "HL52250" in line:
                    qty = int(line[46:53].strip())
                    if qty:
                        moves = self._get_move(
                            reflex_move_ref, product_reflex_code, qty
                        )
                        todo.append((moves, qty))
                elif "HL52165" in line:
                    carrier_code = line[51:63].strip()
            except DataError as e:
                errors.append(str(e))

        if errors:
            if self._context.get("do_not_raise_error"):
                warnings += [
                    "L'import à été forcé, les lignes suivantes n'ont pas "
                    "pu être traité \n"
                ] + errors
            else:
                raise UserError(self._build_error_message(errors, todo))
        self._process_todo(
            todo,
            allow_extra_qty=self._context.get("do_not_raise_error"),
            carrier_code=carrier_code,
        )
        self.attachment_queue_id.description = "\n".join(warnings)


class ProcessorInventory(models.TransientModel):
    _name = "processor.inventory"
    _description = "Processor Inventory"

    @property
    def warehouse_id(self):
        return self._context["warehouse"]

    @property
    def attachment_queue_id(self):
        return self._context["attachment_queue"]

    def run(self, name, string_buffer):
        missings = []
        reader = csv.reader(string_buffer, delimiter=";")
        vals_lines = []
        product2qty = Counter()
        location = self.warehouse_id.lot_stock_id
        inventory = self.env["stock.inventory"].create(
            {
                "name": name,
                "location_ids": [(6, 0, location.ids)],
                # TODO attachment task should have company so attachment queue
                # will have the right company and we should set the company based
                # on the attachment queue
                "company_id": self.warehouse_id.company_id.id,
            }
        )
        inventory.action_start()

        # Note: we only support one location
        lines = {
            (line.product_id, line.prod_lot_id): line for line in inventory.line_ids
        }

        for row in reader:
            product2qty[row[0]] += int(row[1])

        for code, qty in product2qty.items():
            product = self.env["product.product"].search([("reflex_code", "=", code)])
            if not product:
                missings.append((code, qty))
            else:
                # TODO add lot support when we will have case
                line = lines.get((product, self.env["stock.production.lot"]))
                if line:
                    line.product_qty = qty
                else:
                    vals_lines.append(
                        {
                            "product_id": product.id,
                            "product_qty": qty,
                            "location_id": location.id,
                            "inventory_id": inventory.id,
                        }
                    )
        self.env["stock.inventory.line"].create(vals_lines)
        if missings:
            messages = "<p>Les produits suivants n'ont pas été trouvé<br/>"
            messages += "<br/>".join([f"{item[1]} x {item[0]}" for item in missings])
            messages += "</p>"
            inventory.message_post(body=messages)
            self.attachment_queue_id.description = messages.replace("<br/>", "\n")
