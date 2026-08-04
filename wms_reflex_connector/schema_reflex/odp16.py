# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dataclasses import dataclass

from odoo import _

from .base import ReflexLine, ReflexLineDataBase


@dataclass(kw_only=True)
class ReflexLine08110Data(ReflexLineDataBase):
    code_interface: str = "08"
    code_rubrique: str = "110"
    code_recipient: str
    label_recipient: str
    label_recipient_short: str
    director_word_recipient: str
    usage_code_recipient: str = ""
    representative_recipient: str = ""
    representative_phone_0: str = ""
    representative_phone_1: str = ""
    flag_transfer_avail: str = ""
    code_distrib_channel: str
    area_code: str
    code_bank_holiday: str = ""
    code_foreign_language: str = ""
    flag_min_sched_date_management: str
    flag_max_sched_date_management: str
    flag_backorder_allowed: str
    flag_backorder_auto: str
    flag_short_closing_allowed: str
    flag_short_closing_auto: str
    flag_recipient_middleman: str
    flag_globalised_delivery: str
    flag_produce_distribution_sheet: str
    flag_produce_distribution_sheet: str
    flag_produce_delivery_note: str
    flag_produce_palette_sheet: str
    flag_recipient_interface: str
    flag_returnable_load_carrier: str
    code_linked_physical_location: str = ""
    code_support_type: str
    support_maximum_weight: str
    support_maximum_volume: str
    support_standard_volume: str
    flag_split_pickup: str = ""
    flag_generate_interface_shipping_notice: str = ""
    code_shipping_notice_interface_generation_process: str = ""
    flag_detailed_shipping_notice: str = ""
    flag_alloted_shipping_notice: str = ""

    def __post_init__(self):
        if self.flag_backorder_auto == "1" and self.flag_short_closing_auto == "1":
            raise ValueError(
                self.env._(
                    "Flag backorder auto and flag short closing can't be set to one "
                )
            )

        return super().__post_init__()


class ReflexLine08110(ReflexLine):
    def __init__(
        self,
        data: ReflexLine08110Data,
    ):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code destinataire", 13, data.code_recipient),
            (
                "Libellé destinataire",
                30,
                data.label_recipient,
                {"truncate_silent": True},
            ),
            (
                "Libellé réduit destinataire",
                15,
                data.label_recipient_short,
                {"truncate_silent": True},
            ),
            ("Code destinataire", 15, data.director_word_recipient),
            ("Code d'usage destinataire", 13, data.usage_code_recipient),
            ("Interlocuteur destinataire", 30, data.representative_recipient),
            ("Téléphone interlocuteur", 15, data.representative_phone_0),
            ("Télécopie interlocuteur", 15, data.representative_phone_1),
            ("Top transferts possibles", 1, data.flag_transfer_avail),
            ("Code circuit de distribution", 3, data.code_distrib_channel),
            ("Code région", 6, data.area_code),
            ("Code famille jours fériés", 3, data.code_bank_holiday),
            ("Code langue étrangère", 3, data.code_foreign_language),
            (
                "Top gestion date ordonnancement mini",
                1,
                data.flag_min_sched_date_management,
            ),
            (
                "Top gestion date ordonnancement supérieure",
                1,
                data.flag_max_sched_date_management,
            ),
            ("Top reliquat possible", 1, data.flag_backorder_allowed),
            ("Top reliquat automatique", 1, data.flag_backorder_auto),
            ("Top solde possible", 1, data.flag_short_closing_allowed),
            ("Top solde automatique", 1, data.flag_short_closing_auto),
            ("Top destinataire intermédiaire", 1, data.flag_recipient_middleman),
            ("Top livraison globalisée", 1, data.flag_globalised_delivery),
            (
                "Top édition bordereau d'éclatement",
                1,
                data.flag_produce_distribution_sheet,
            ),
            ("Top édition BL finaux", 1, data.flag_produce_distribution_sheet),
            ("Top édition 'fiche palette'", 1, data.flag_produce_delivery_note),
            ("Top interface pour le destinataire", 1, data.flag_produce_palette_sheet),
            ("Top agrès consignés", 1, data.flag_recipient_interface),
            ("Code dépôt physique correspondant", 3, data.flag_returnable_load_carrier),
            ("Code type de support", 3, data.code_linked_physical_location),
            ("Poids maximum support", 11, data.code_support_type),
            ("Volume maximum support", 11, data.support_maximum_weight),
            ("Volume standard support", 11, data.support_maximum_volume),
            ("Top scinder prélèvement", 1, data.support_standard_volume),
            ("Top interface avis d'expédition à générer", 1, data.flag_split_pickup),
            (
                "Code chaîne génération interface avis d'expédition",
                15,
                data.flag_generate_interface_shipping_notice,
            ),
            (
                "Top avis d'expédition détaillé",
                1,
                data.code_shipping_notice_interface_generation_process,
            ),
            ("Top avis d'expédition alloti", 1, data.flag_detailed_shipping_notice),
        ]


@dataclass(kw_only=True)
class ReflexLine08111Data(ReflexLineDataBase):
    code_interface: str = "08"
    code_rubrique: str = "111"
    dest_partner_code: str
    address_code: str = ""
    dest_partner_label: str
    dest_partner_address: str
    dest_partner_address_more: str = ""
    postal_code: str
    city: str
    country_code: str
    dest_partner_phone: str = ""
    dest_partner_fax: str = ""
    dest_partner_other_number: str = ""

    def __post_init__(self):
        self.dest_partner_address = self.dest_partner_address or "."
        return super().__post_init__()


class ReflexLine08111(ReflexLine):
    def __init__(self, data: ReflexLine08111Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code destinataire", 13, data.dest_partner_code),
            ("Code adresse", 13, data.address_code),
            (
                "Raison social",
                30,
                data.dest_partner_label,
                {"truncate_silent": True},
            ),
            (
                "Adresse 1 destinataire",
                30,
                data.dest_partner_address,
                {"truncate_silent": True},
            ),
            (
                "Adresse 2 destinataire",
                30,
                data.dest_partner_address_more,
                {"truncate_silent": True},
            ),
            ("Adresse 3 destinataire - CP", 9, data.postal_code),
            (
                "Adresse 3 destinataire - Ville",
                21,
                data.city,
                {"truncate_silent": True},
            ),
            ("Adresse 4 destinataire", 30, data.country_code),
            ("Téléphone destinataire", 15, data.dest_partner_phone),
            ("Télécopie destinataire", 15, data.dest_partner_fax),
            ("Autre numéro destinataire", 10, data.dest_partner_other_number),
        ]


@dataclass(kw_only=True)
class ReflexLine16110Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "110"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    preparation_type_code: str = "010"
    unused_1: str = ""
    dest_partner_code: str
    dest_ref: str
    expected_date: str
    requested_delivery_start_time: str = ""
    requested_delivery_end_time: str = ""
    requested_delivery_date_type: str = "010"
    final_delivery_expected_date: str = ""
    final_delivery_start_time: str = ""
    final_delivery_end_time: str = ""
    global_delivery_flag: str = ""
    picking_circuit_code: str = "001"
    launch_date: int = 0
    launch_code: str = ""
    loading_date: int = 0
    loading_code: str = ""
    availability_location_1: str = ""
    availability_location_2: str = ""
    availability_location_3: str = ""
    availability_location_4: str = ""
    availability_location_5: str = ""
    intermediate_recipient_flag: str = "0"
    intermediate_recipient_code: str = ""
    intermediate_recipient_ref: str = ""
    intermediate_delivery_date: str = ""
    intermediate_delivery_start_time: str = ""
    intermediate_delivery_end_time: str = ""
    distribution_sheet_flag: str = ""
    final_delivery_note_flag: str = ""
    protected_odp_flag: str = "0"
    automatic_generation_flag: str = "0"
    transport_quality_code: str = ""
    stock_out_validation_flag: str = ""
    preparation_family_code: str = ""
    reservation_ref: str = ""
    estimated_deliv_date: str = ""

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        return super().__post_init__()


class ReflexLine16110(ReflexLine):
    def __init__(self, data: ReflexLine16110Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("Code type de préparation", 3, data.preparation_type_code),
            ("NON UTILISE", 12, data.unused_1),
            ("Code destinataire final", 13, data.dest_partner_code),
            ("Référence destinataire final", 20, data.dest_ref),
            # Livraison demandée
            ("Date de livraison demandée", 8, data.expected_date),
            ("Heure début livraison demandée", 4, data.requested_delivery_start_time),
            ("Heure fin livraison demandée", 4, data.requested_delivery_end_time),
            ("Type date de livraison demandée", 3, data.requested_delivery_date_type),
            # Prévue livraison finale
            ("Date prévue de livraison finale", 8, data.final_delivery_expected_date),
            ("Heure début livraison finale", 4, data.final_delivery_start_time),
            ("Heure fin livraison finale", 4, data.final_delivery_end_time),
            ("Top livraison globalisée", 1, data.global_delivery_flag),
            ("Code circuit de prélèvement", 10, data.picking_circuit_code),
            # Lancement
            ("Date de lancement", 8, data.launch_date),
            ("Code lancement", 3, data.launch_code),
            # Chargement
            ("Date de chargement", 8, data.loading_date),
            ("Code chargement", 6, data.loading_code),
            ("Emplacement 1 de mise à disposition", 4, data.availability_location_1),
            ("Emplacement 2 de mise à disposition", 1, data.availability_location_2),
            ("Emplacement 3 de mise à disposition", 3, data.availability_location_3),
            ("Emplacement 4 de mise à disposition", 2, data.availability_location_4),
            ("Emplacement 5 de mise à disposition", 2, data.availability_location_5),
            ("Top destinataire intermédiaire", 1, data.intermediate_recipient_flag),
            ("Code destinataire intermédiaire", 13, data.intermediate_recipient_code),
            (
                "Référence destinataire intermédiaire",
                20,
                data.intermediate_recipient_ref,
            ),
            # Livraison intermédiaire
            ("Date de livraison intermédiaire", 8, data.intermediate_delivery_date),
            (
                "Heure début livraison intermédiaire",
                4,
                data.intermediate_delivery_start_time,
            ),
            (
                "Heure fin livraison intermédiaire",
                4,
                data.intermediate_delivery_end_time,
            ),
            ("Top édition bordereau d'éclatement", 1, data.distribution_sheet_flag),
            ("Top édition des BL finaux", 1, data.final_delivery_note_flag),
            ("Top ODP protégé", 1, data.protected_odp_flag),
            ("Top génération automatique", 1, data.automatic_generation_flag),
            ("Code qualité transport", 3, data.transport_quality_code),
            (
                "Top sortie de stock à la validation de préparation",
                1,
                data.stock_out_validation_flag,
            ),
            ("Code famille de préparation", 3, data.preparation_family_code),
            ("Référence de réservation", 20, data.reservation_ref),
        ]


@dataclass(kw_only=True)
class ReflexLine16111Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "111"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    final_recipient_appointment_taken_flag: str = "0"
    final_recipient_appointment_century: int = 0
    final_recipient_appointment_year: int = 0
    final_recipient_appointment_month: int = 0
    final_recipient_appointment_day: int = 0
    final_recipient_appointment_start_time: int = 0
    final_recipient_appointment_end_time: int = 0
    intermediate_recipient_appointment_taken_flag: str = "0"
    intermediate_recipient_appointment_century: int = 0
    intermediate_recipient_appointment_year: int = 0
    intermediate_recipient_appointment_month: int = 0
    intermediate_recipient_appointment_day: int = 0
    intermediate_recipient_appointment_start_time: int = 0
    intermediate_recipient_appointment_end_time: int = 0
    preparation_order_reason: str = ""
    planned_preparation_century: int = 0
    planned_preparation_year: int = 0
    planned_preparation_month: int = 0
    planned_preparation_day: int = 0
    loading_group: str = ""
    shipping_group: str = ""
    reservation_end_century: int = 0
    reservation_end_year: int = 0
    reservation_end_month: int = 0
    reservation_end_day: int = 0
    reservation_end_time: int = 0

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        return super().__post_init__()


class ReflexLine16111(ReflexLine):
    def __init__(self, data: ReflexLine16111Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            (
                "Top RV pris destinataire final",
                1,
                data.final_recipient_appointment_taken_flag,
            ),
            # RV Destinataire final
            (
                "Date RV destinataire final - Siècle",
                2,
                data.final_recipient_appointment_century,
            ),
            (
                "Date RV destinataire final - Année",
                2,
                data.final_recipient_appointment_year,
            ),
            (
                "Date RV destinataire final - Mois",
                2,
                data.final_recipient_appointment_month,
            ),
            (
                "Date RV destinataire final - Jour",
                2,
                data.final_recipient_appointment_day,
            ),
            (
                "Heure début RV destinataire final",
                4,
                data.final_recipient_appointment_start_time,
            ),
            (
                "Heure fin RV destinataire final",
                4,
                data.final_recipient_appointment_end_time,
            ),
            # RV Destinataire intermédiaire
            (
                "Top RV pris destinataire intermédiaire",
                1,
                data.intermediate_recipient_appointment_taken_flag,
            ),
            (
                "Date RV destinataire intermédiaire - Siècle",
                2,
                data.intermediate_recipient_appointment_century,
            ),
            (
                "Date RV destinataire intermédiaire - Année",
                2,
                data.intermediate_recipient_appointment_year,
            ),
            (
                "Date RV destinataire intermédiaire - Mois",
                2,
                data.intermediate_recipient_appointment_month,
            ),
            (
                "Date RV destinataire intermédiaire - Jour",
                2,
                data.intermediate_recipient_appointment_day,
            ),
            (
                "Heure début RV destinataire intermédiaire",
                4,
                data.intermediate_recipient_appointment_start_time,
            ),
            (
                "Heure fin RV destinataire intermédiaire",
                4,
                data.intermediate_recipient_appointment_end_time,
            ),
            ("Motif ordre de préparation", 3, data.preparation_order_reason),
            (
                "Date de préparation prévue - Siècle",
                2,
                data.planned_preparation_century,
            ),
            (
                "Date de préparation prévue - Année",
                2,
                data.planned_preparation_year,
            ),
            (
                "Date de préparation prévue - Mois",
                2,
                data.planned_preparation_month,
            ),
            (
                "Date de préparation prévue - Jour",
                2,
                data.planned_preparation_day,
            ),
            ("Regroupement chargement", 10, data.loading_group),
            ("Regroupement expédition", 13, data.shipping_group),
            ("Date de fin de réservation - Siècle", 2, data.reservation_end_century),
            ("Date de fin de réservation - Année", 2, data.reservation_end_year),
            ("Date de fin de réservation - Mois", 2, data.reservation_end_month),
            ("Date de fin de réservation - Jour", 2, data.reservation_end_day),
            ("Heure de fin de réservation", 4, data.reservation_end_time),
        ]


class ReflexLine1611A(ReflexLine):
    def __init__(
        self,
        sequence,
        internal_ref,
        partner_name,
        street,
        street2,
        street3,
        city,
        postal_zip,
        country_code,
    ):
        self.sequence = sequence
        self.internal_ref = internal_ref
        self.partner_name = partner_name
        self.street = street
        self.street2 = street2 or ""
        self.street3 = street3 or ""
        self.city = city
        self.zip = postal_zip
        self.country_code = country_code

    def get_values(self):
        return [
            ("N° de séquence", 7, self.sequence),
            ("Code application", 2, "HL"),
            ("Code interface", 2, "16"),
            ("Rubrique", 3, "11A"),
            ("Code activité", 3, "164"),
            ("Code dépôt physique", 3, "023"),
            ("Code donneur d'ordres", 13, "164"),
            ("Référence donneur d'ordres", 20, self.internal_ref),
            ("Code type d’adresse", 3, "010"),
            ("Nom de l’adresse ou Raison Sociale", 35, self.partner_name),
            ("Rue et n° et/ou Boîte Postale", 35, self.street),
            ("Complément d’adresse 1", 35, self.street2),
            ("Complément d’adresse 2", 35, self.street3),
            ("Nom de la localité", 35, self.city),
            ("Code de la division territoriale", 9),
            ("Code postal", 9, self.zip),
            ("Code pays ISO", 3, self.country_code),
        ]


@dataclass(kw_only=True)
class ReflexLine16114Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "114"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    contact_type_code: str = "010"
    civil_status_code: int = 1
    firstname: str
    lastname: str
    address_type_1_code: str = "010"
    email: str = ""

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        self.firstname = self.firstname or "."
        self.lastname = self.lastname or "."
        self.email = self.email or ""
        return super().__post_init__()


class ReflexLine16114(ReflexLine):
    def __init__(self, data: ReflexLine16114Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("Code type de contact", 3, data.contact_type_code),
            ("Code civilité", 1, data.civil_status_code),
            ("Prénom du contact", 35, data.firstname),
            ("Nom du contact", 35, data.lastname),
            ("Code type d'adresse 1", 3, data.address_type_1_code),
            ("Adresse 1 du contact", 140, data.email),
        ]


@dataclass(kw_only=True)
class ReflexLine16115Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "115"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    contact_type_code: str = "010"
    partner_mobile: str = ""
    partner_phone: str = ""
    fax_number: str = ""

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        self.partner_mobile = self.partner_mobile or ""
        self.partner_phone = self.partner_phone or ""
        return super().__post_init__()


class ReflexLine16115(ReflexLine):
    def __init__(self, data: ReflexLine16115Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("Code type de contact", 3, data.contact_type_code),
            ("Numéro de téléphone mobile", 20, data.partner_mobile),
            ("Numéro de téléphone fixe", 20, data.partner_phone),
            ("Numéro de fax", 20),
        ]


@dataclass(kw_only=True)
class ReflexLine16119Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "119"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    comment_line_index: str
    comment_family: str
    comment: str

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        return super().__post_init__()


class ReflexLine16119(ReflexLine):
    def __init__(self, data: ReflexLine16119Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("N° ligne commentaire", 3, data.comment_line_index),
            ("Famille de commentaire", 3, data.comment_family),
            ("Commentaire", 70, data.comment),
        ]


@dataclass(kw_only=True)
class ReflexLine16120Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "120"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    line_index: int
    product_code: str
    article_vl_code: str = "10"
    packaging_recipient_ref: str = ""
    vl_command_ref: str = ""
    qty: float
    preparation_qty_level_2: str = ""
    preparation_qty_level_3: str = ""
    preparation_net_weight: str = ""
    preparation_gross_weight: str = ""
    preparation_volume: str = ""
    preparation_owner_code: str = ""
    preparation_quality_code: str = "STD"
    order_info_entered_flag: str = "0"
    ordered_qty_level_2: str = ""
    ordered_qty_level_3: str = ""
    ordered_base_or_order_vl_qty: str = ""
    ordered_net_weight: str = ""
    ordered_gross_weight: str = ""
    ordered_volume: str = ""
    ordered_owner_code: str = ""
    ordered_quality_code: str = "STD"
    stock_reservation_flag: int = 0
    service_priority_code: str = ""
    forced_min_scheduling_delay_flag: int = 0
    min_scheduling_days: int = 0
    chaining_possible_flag: int = 0
    substitution_possible_flag: int = 0
    lot_1: str = ""
    base_vl_quantity_flag: int = 0
    indifferent_vl_flag: int = 0

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        return super().__post_init__()


class ReflexLine16120(ReflexLine):
    def __init__(self, data: ReflexLine16120Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("N° ligne référence donneur d'ordres", 7, data.line_index),
            ("Code article", 16, data.product_code),
            ("Code VL article", 2, data.article_vl_code),
            (
                "Référence conditionnement destinataire",
                20,
                data.packaging_recipient_ref,
            ),
            ("Référence de commande de la VL", 16, data.vl_command_ref),
            ("Quantité niveau 1 à préparer", 7, data.qty, {"decimal": 0}),
            ("Quantité niveau 2 à préparer", 7, data.preparation_qty_level_2),
            ("Quantité niveau 3 à préparer", 7, data.preparation_qty_level_3),
            (
                "Quantité à préparer en VL de base (ou en VL de commande)",
                7,
                data.qty,
                {"decimal": 0},
            ),
            ("Poids net à préparer", 9, data.preparation_net_weight),
            ("Poids brut à préparer", 9, data.preparation_gross_weight),
            ("Volume à préparer", 9, data.preparation_volume),
            ("Code propriétaire à préparer", 3, data.preparation_owner_code),
            ("Code qualité à préparer", 3, data.preparation_quality_code),
            ("Top infos commande saisies", 1, data.order_info_entered_flag),
            ("Quantité niveau 1 commandée", 7, data.qty),
            ("Quantité niveau 2 commandée", 7, data.ordered_qty_level_2),
            ("Quantité niveau 3 commandée", 7, data.ordered_qty_level_3),
            (
                "Quantité commandée en VL de base ou en VL de commande",
                7,
                data.ordered_base_or_order_vl_qty,
            ),
            ("Poids net commandé", 9, data.ordered_net_weight),
            ("Poids brut commandé", 9, data.ordered_gross_weight),
            ("Volume commandé", 9, data.ordered_volume),
            ("Code propriétaire commandé", 3, data.ordered_owner_code),
            ("Code qualité commandée", 3, data.ordered_quality_code),
            ("Top réservation stock", 1, data.stock_reservation_flag),
            ("Code priorité de service", 1, data.service_priority_code),
            (
                "Top délai mini date ordo forcée",
                1,
                data.forced_min_scheduling_delay_flag,
            ),
            ("Nb jours mini date ordo forcée", 3, data.min_scheduling_days),
            ("Top chaînage possible", 1, data.chaining_possible_flag),
            ("Top substitution possible", 1, data.substitution_possible_flag),
            ("Lot 1", 20, data.lot_1),
            ("Top quantité VL de base", 1, data.base_vl_quantity_flag),
            ("Top VL indifférente", 1, data.indifferent_vl_flag),
        ]


@dataclass(kw_only=True)
class ReflexLine16129Data(ReflexLineDataBase):
    code_interface: str = "16"
    code_rubrique: str = "129"
    physical_depot_code: str = "023"
    ordering_party_code: str = "164"
    internal_ref: str
    line_index: int
    comment_line_number: str = "001"
    comment_family: str = ""
    comment: str = ""

    def __post_init__(self):
        self.internal_ref = self.internal_ref or ""
        return super().__post_init__()


class ReflexLine16129(ReflexLine):
    def __init__(self, data: ReflexLine16129Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, data.physical_depot_code),
            ("Code donneur d'ordres", 13, data.ordering_party_code),
            ("Référence donneur d'ordres", 20, data.internal_ref),
            ("N° ligne référence donneur d'ordres", 7, data.line_index),
            ("N° de ligne commentaire", 3, data.comment_line_number),
            ("Famille de commentaire", 3, data.comment_family),
            ("Commentaire", 70, data.comment),
        ]
