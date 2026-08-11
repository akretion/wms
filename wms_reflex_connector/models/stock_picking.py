# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import groupby

from ..schema_reflex.odp16 import (
    ReflexLine08110,
    ReflexLine08111,
    ReflexLine1611A,
    ReflexLine16110,
    ReflexLine16111,
    ReflexLine16114,
    ReflexLine16115,
    ReflexLine16119,
    ReflexLine16120,
)
from ..schema_reflex.rec32 import (
    ReflexLine12110,
    ReflexLine12111,
    ReflexLine32110,
    ReflexLine32120,
)


class StockPicking(models.Model):
    _inherit = ["reflex.exportable.mixin", "stock.picking"]
    _name = "stock.picking"

    @property
    def file_creation_mode(self):
        return "per_record"

    def _prepare_export_data(self, sequence):
        self.ensure_one()
        if self.picking_type_id.code == "incoming":
            return self._prepare_in_export_data(sequence)
        elif self.picking_type_id.code == "outgoing":
            return self._prepare_out_export_data(sequence)

    def _prepare_in_export_data(self, sequence):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("L'expéditeur est manquant, veuillez le renseigner")
        picking_name = self.name.split("/")[-1]
        lines = [
            ReflexLine12110(
                sequence=sequence,
                code_seller=self.partner_id.id,
                name_seller=self.partner_id.name,
            ),
            ReflexLine12111(
                sequence=sequence,
                code_seller=self.partner_id.id,
                name_seller=self.partner_id.name,
                address=self.partner_id.street,
                zip_code=self.partner_id.zip,
                city=self.partner_id.city,
                country_code=self.partner_id.country_id.code,
            ),
            ReflexLine32110(
                sequence=sequence,
                code_seller=self.partner_id.id,
                origin=self.origin or picking_name,
                delivery_order_number=picking_name,
                delivery_date=self.scheduled_date,
            ),
        ]
        for i, move_line in enumerate(self.move_lines):
            move_line.product_id.check_reflex_exported()
            move_line._check_qty_not_null()
            lines += [
                ReflexLine32120(
                    sequence=sequence,
                    code_seller=self.partner_id.id,
                    origin=self.origin or picking_name,
                    delivery_order_number=picking_name,
                    line_sequence=(i + 1) * 100,
                    product_code=move_line.product_id.reflex_code,
                    qty=move_line.product_qty,
                ),
                # ReflexLine32129(sequence, self.partner_id.id, self.name, 1, "", ""),
            ]

        return [line.render() for line in lines]

    def _check_address_valid(self):
        partner = self.partner_id
        if not partner.name:
            raise UserError("Le nom du client sur l'adresse est vide")
        if not partner.street:
            raise UserError("Le premier champs rue de l'adresse est vide")
        if not partner.city:
            raise UserError("Le champs ville de l'adresse est vide")
        if not partner.zip:
            raise UserError("Le champs zip de l'adresse est vide")
        if not partner.country_id:
            raise UserError("Le champs pays de l'adresse est vide")

    def _prepare_out_export_data(self, sequence):
        self.ensure_one()
        self._check_address_valid()
        if not set(self.move_lines.mapped("state")) <= {"assigned", "done"}:
            raise UserError(
                "Vous ne pouvez pas exporter un bon de livraison "
                "qui n'est pas disponible en stock"
            )
        sequence = 1
        lines = []
        partner = self.partner_id
        # In case we have agent on line we group then in different pack
        # each pack will be a "picking" for reflex
        # so we generate a "pack_ref" that will be used as "picking_ref"(=internal_ref)
        # for line without agent, the partner is used
        for agent, move_lines in groupby(self.move_lines, lambda s: s.dest_contact_id):
            # Use sale name or rma name (in origin) or picking name
            if not agent:
                if partner.parent_id and partner.parent_id.name != partner.name:
                    dest_partner_label = partner.display_name
                else:
                    dest_partner_label = partner.name
                agent = partner
                pack_ref = f"{self.name}-0"
            else:
                dest_partner_label = agent.name
                pack_ref = f"{self.name}-{sequence}"
                sequence += 1

            partner_name, street1, street2, street3 = partner._get_wms_delivery_info()
            lines += [
                ReflexLine08110(
                    sequence=sequence,
                    dest_partner_code=agent.id,
                    dest_partner_label=dest_partner_label,
                    dest_partner_short_label=agent.lastname,
                ),
                ReflexLine08111(
                    sequence=sequence,
                    dest_partner_code=agent.id,
                    dest_partner_label=dest_partner_label,
                    dest_partner_address=partner.street,
                    dest_partner_address_more=partner.street2,
                    postal_code=partner.zip,
                    city=partner.city,
                    country_code=partner.country_id.code,
                ),
                ReflexLine16110(
                    sequence=sequence,
                    internal_ref=pack_ref,
                    dest_ref=self.origin or self.name,
                    dest_partner_code=agent.id,
                    expected_date=self.date,
                    estimated_deliv_date=self.date,
                ),
                ReflexLine16111(
                    sequence=sequence,
                    internal_ref=pack_ref,
                ),
                ReflexLine1611A(
                    sequence=sequence,
                    internal_ref=pack_ref,
                    partner_name=partner_name,
                    street=street1,
                    street2=street2,
                    street3=street3,
                    city=partner.city,
                    postal_zip=partner.zip,
                    country_code=partner.country_id.code,
                ),
                ReflexLine16114(
                    sequence=sequence,
                    internal_ref=pack_ref,
                    gender=agent.genre_id.code,
                    firstname=agent.firstname,
                    lastname=agent.lastname,
                    email=partner.email,  # do not send personnal agent email
                ),
                ReflexLine16115(
                    sequence=sequence,
                    internal_ref=pack_ref,
                    partner_mobile=partner.mobile,
                    partner_phone=partner.phone,
                ),
            ]
            if self.sale_id.ej_number:
                lines.append(
                    ReflexLine16119(
                        sequence=sequence,
                        internal_ref=pack_ref,
                        comment_line_index=1,
                        comment_family="VA1",
                        comment=self.sale_id.ej_number,
                        # chorus: custom_facturx
                    )
                )
            if self.sale_id.client_order_ref:
                lines.append(
                    ReflexLine16119(
                        sequence=sequence,
                        internal_ref=pack_ref,
                        comment_line_index=2,
                        comment_family="VA2",
                        comment=self.sale_id.client_order_ref,
                    )
                )
            if self.sale_id.contract_id.name:
                lines.append(
                    ReflexLine16119(
                        sequence=sequence,
                        internal_ref=pack_ref,
                        comment_line_index=3,
                        comment_family="VA3",
                        comment=self.sale_id.contract_id.name,
                        # module: sale_team_contract
                    )
                )
            if self.note_alaine:
                padded = self.note_alaine.ljust(140)
                chunks = {"VA4": padded[:70], "VA5": padded[70:]}
                for index, (key, chunk) in enumerate(chunks.items(), start=4):
                    if not chunk.strip():
                        continue
                    lines.append(
                        ReflexLine16119(
                            sequence=sequence,
                            internal_ref=pack_ref,
                            comment_line_index=index,
                            comment_family=key,
                            comment=chunk,
                        )
                    )
            # TODO
            #  ReflexLine16119(
            #      sequence=sequence,
            #      internal_ref=pack_ref,
            #      comment_line_index=4,
            #      comment_family="TRP",
            #      comment="",
            #      # mode de transport
            #  )
            #  ReflexLine16119(
            #      sequence=sequence,
            #      internal_ref=pack_ref,
            #      comment_line_index=5,
            #      comment_family="ICO",
            #      comment="",
            #      # incoterm
            #  )
            #  ReflexLine16119(
            #      sequence=sequence,
            #      internal_ref=pack_ref,
            #      comment_line_index=6,
            #      comment_family="ICV",
            #      comment="",
            #      # incorterm ville
            #  )

            for index, move_line in enumerate(move_lines):
                move_line.reflex_reference = pack_ref
                move_line.product_id.check_reflex_exported()
                move_line._check_qty_not_null()
                lines.append(
                    ReflexLine16120(
                        sequence=sequence,
                        internal_ref=pack_ref,
                        line_index=index * 100,
                        product_code=move_line.product_id.reflex_code,
                        qty=move_line.product_qty,
                    ),
                )
                # Put back in once we know what the values are
                # lines.append(
                #     ReflexLine16129(
                #         sequence=sequence,
                #         internal_ref=pack_ref,
                #         line_index=index * 100,
                #     ),
                # )

        return [line.render() for line in lines]

    def _get_export_name(self):
        if self.picking_type_id.code == "incoming":
            return f"AEX_{self.name.replace('/', '_')}.in"
        elif self.picking_type_id.code == "outgoing":
            return f"ODP_{self.name.replace('/', '_')}.in"

    def _is_user_allowed_to_validate(self):
        return True

    def button_validate(self):
        for record in self:
            if (
                record.is_wms_exportable
                and not record._context.get("validation_from_sync")
                and not self._is_user_allowed_to_validate()
            ):
                raise UserError("Vous n'avez pas les droits de valider ce transfert")
        return super().button_validate()
