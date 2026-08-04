# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dataclasses import dataclass

from .base import ReflexLine, ReflexLineDataBase

LOT_MAPPING = {
    False: "001",  # in case that lot value is empty
    "none": "001",
    "lot_dluo": "002",
    "lot": "003",
    "lot_fab": "004",
}


@dataclass(kw_only=True)
class ReflexLine03110Data(ReflexLineDataBase):
    code_interface: str = "03"
    code_rubrique: str = "110"
    code_article: str
    label: str = ""
    label_short: str = ""
    director_word: str = ""
    usage_code: str = ""
    tag_article: str = ""
    flag_article_variable_weight: str = ""
    flag_article_returnable: str = ""
    flag_article_alcohol: str = ""
    flag_article_dangerous: str = ""
    number_of_stabilisation_days: str = ""
    min_days_to_scheduling: str = ""
    range_sched_date_stock: str = ""
    range_sched_date_for_prep: str = ""
    code_expiry_family: str = ""
    ref_base_code: str = ""
    variant_type_code: str = ""
    flag_detailed_weight_at_receipt: str = ""
    flag_detailed_weight_at_prep: str = ""
    flag_prepacking: str = ""
    flag_new_article: str = ""


class ReflexLine03110(ReflexLine):
    def __init__(self, reflex_line_data: ReflexLine03110Data, update: bool):
        super().__init__()
        self.data = reflex_line_data
        self.update = update

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code article", 16, data.code_article),
            ("Libellé", 30, data.label, {"truncate_silent": True}),
            ("Libellé réduit", 15, data.label_short),
            ("Mot directeur", 15, data.director_word),
            ("Code d'usage", 16, data.usage_code),
            ("Marquage article", 16, data.tag_article),
            ("Top article poids variable", 1, data.flag_article_variable_weight),
            ("Top article consigne", 1, data.flag_article_returnable),
            ("Top article alcool", 1, data.flag_article_alcohol),
            ("Top article dangereux", 1, data.flag_article_dangerous),
            ("Nombre de jours stabilisation", 3, data.number_of_stabilisation_days),
            ("Nombre de jours mini date d'ordo", 3, data.min_days_to_scheduling),
            ("Fourchette banal date ordo pour stock", 5, data.range_sched_date_stock),
            ("Fourchette banal date ordo pour prép", 5, data.range_sched_date_for_prep),
            ("Code famille de péremption", 3, data.code_expiry_family),
            ("Code référence de base", 16, data.ref_base_code),
            ("Code type de VL", 3, data.variant_type_code),
            ("Top poids détaillé à la récep", 1, data.flag_detailed_weight_at_receipt),
            ("Top poids détaillé à la prép", 1, data.flag_detailed_weight_at_prep),
            ("Top pose à plat / précolisage", 1, data.flag_prepacking),
            ("Top article nouveau", 1, int(not self.update)),
        ]


@dataclass(kw_only=True)
class ReflexLine03112Data(ReflexLineDataBase):
    code_interface: str = "O3"
    code_rubrique: str = "112"
    code_article: str
    article_description: str = ""


class ReflexLine03112(ReflexLine):
    def __init__(self, data: ReflexLine03112Data):
        super().__init__()
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_activity),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code article", 16, data.code_article),
            ("Descriptif de l’article", 230, data.article_description),
        ]


@dataclass(kw_only=True)
class ReflexLine03119Data(ReflexLineDataBase):
    code_interface: str = "O3"
    code_rubrique: str = "119"
    code_article: str
    num_comment_line: str
    num_comment_family: str
    comment: str


class ReflexLine03119(ReflexLine):
    def __init__(self, data: ReflexLine03119Data):
        super().__init__()
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code article", 16, data.code_article),
            ("N° ligne commentaire", 3, data.num_comment_line),
            ("Famille de commentaire", 3, data.num_comment_family),
            ("Commentaire", 70, data.comment),
        ]


@dataclass(kw_only=True)
class ReflexLine03120Data(ReflexLineDataBase):
    code_interface: str = "O3"
    code_rubrique: str = "120"
    code_article: str
    code_log_var: str
    director_word: str
    usage_code: str = ""
    code_type_log_var: str
    flag_base_log_var: str = "0"
    flag_packaging_log_var: str = ""
    code_log_var_subpackaging: str = ""
    quantity_log_var_subpackaging: str = ""
    log_var_order_ref: str = ""
    net_weight: str = ""
    raw_weight: str = ""
    height: str = ""
    width: str = ""
    depth: str = ""
    volume: str = ""
    standard_price: str = ""
    flag_receipt_control: str = ""
    flag_receipt_repackaging: str = ""
    code_support_type: str = ""
    code_location_size: str = ""
    standard_number_of_packaging: str = ""
    flag_automatic_supports_link: str = ""
    code_stock_family: str = ""
    code_mass_stock_family: str = ""
    num_log_var_for_layer: str = ""
    layer_height: str = ""
    code_prep_family: str = ""
    packaging_start_date_century: str = ""
    packaging_start_date_year: str = ""
    packaging_start_date_month: str = ""
    packaging_start_date_day: str = ""
    packaging_end_date_century: str = ""
    packaging_end_date_year: str = ""
    packaging_end_date_month: str = ""
    packaging_end_date_day: str = ""
    flag_management_log_var: str = ""
    flag_kit: str = ""
    flag_new_log_var: str = ""
    code_on_layer_constraint: str = ""
    on_layer_allowed_weight: str = ""
    code_on_partial_layer_constraint: str = ""


class ReflexLine03120(ReflexLine):
    def __init__(self, data: ReflexLine03120Data):
        super().__init__()
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code article", 16, data.code_article),
            ("Code variante logistique", 2, data.code_log_var),
            ("Mot directeur", 15, data.director_word, {"truncate_silent": True}),
            ("Code d'usage", 16, data.usage_code),  # unused
            ("Code type de VL", 3, data.code_type_log_var),
            ("Top VL de base", 1, data.flag_base_log_var),
            ("Top VL de conditionnement", 1, data.flag_packaging_log_var),
            ("Code VL de sous-conditionnement", 2, data.code_log_var_subpackaging),
            (
                "Quantité en VL de sous-conditionnement",
                7,
                data.quantity_log_var_subpackaging,
            ),
            ("Référence de commande de la VL", 16, data.log_var_order_ref),
            ("Poids net", 9, data.net_weight, {"decimal": 3}),
            ("Poids brut", 9, data.raw_weight),
            ("Hauteur", 7, data.height),
            ("Largeur", 7, data.width),
            ("Profondeur", 7, data.depth),
            ("Volume", 7, data.volume, {"empty_if_zero": True}),
            ("Prix standard", 11, data.standard_price),
            ("Top contrôle à réception", 1, "0", data.flag_receipt_control),
            (
                "Top reconditionnement à réception",
                1,
                "0",
                data.flag_receipt_repackaging,
            ),
            ("Code type support", 3, data.code_support_type),
            ("Code taille emplacement", 3, data.code_location_size),
            (
                "Stockage standard : nombre de conditionnements",
                2,
                data.standard_number_of_packaging,
            ),  # unused
            (
                "Top association automatique supports",
                1,
                data.flag_automatic_supports_link,
            ),
            ("Code famille de stockage", 3, data.code_stock_family),
            ("Code famille de stockage masse", 6, data.code_mass_stock_family),
            (
                "Nb VL de sous-conditionnement pour constituer une couche",
                7,
                data.num_log_var_for_layer,
            ),
            ("Hauteur d'une couche", 7, data.layer_height),
            ("Code famille de préparation", 3, data.code_prep_family),
            (
                "Date début service conditionnement - Siècle",
                2,
                data.packaging_start_date_century,
            ),
            (
                "Date début service conditionnement - Année",
                2,
                data.packaging_start_date_year,
            ),
            (
                "Date début service conditionnement - Mois",
                2,
                data.packaging_start_date_month,
            ),
            (
                "Date début service conditionnement - Jour",
                2,
                data.packaging_start_date_day,
            ),
            (
                "Date fin service conditionnement - Siècle",
                2,
                data.packaging_end_date_century,
            ),
            (
                "Date fin service conditionnement - Année",
                2,
                data.packaging_end_date_year,
            ),
            (
                "Date fin service conditionnement - Mois",
                2,
                data.packaging_end_date_month,
            ),
            ("Date fin service conditionnement - Jour", 2, data.packaging_end_date_day),
            ("Top VL de gestion", 1, data.flag_management_log_var),
            ("Top kit", 1, data.flag_kit),
            ("Top VL nouvelle", 1, data.flag_new_log_var),
            (
                "Code contrainte de pose sur couche complète",
                3,
                data.code_on_layer_constraint,
            ),
            (
                "Poids supporté par une couche complète",
                11,
                data.on_layer_allowed_weight,
            ),
            (
                "Code contrainte de pose sur couche incomplète (Reflex Web uniquement)",
                3,
                data.code_on_partial_layer_constraint,
            ),
        ]
