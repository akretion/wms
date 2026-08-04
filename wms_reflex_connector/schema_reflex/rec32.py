# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .base import ReflexLine, ReflexLineDataBase


class ReflexLine12110Data(ReflexLineDataBase):
    code_interface: str = "12"
    code_rubrique: str = "110"
    code_seller: str
    label_seller: str
    label_short_seller: str
    director_word_seller: str
    usage_code_seller: str = ""
    representative: str = ""
    representative_phone: str = ""
    representative_fax: str = ""
    code_load_carrier_assignment: str
    customs_delay: str = ""
    linked_physical_location: str = ""
    flag_packaging_control_seller: str


class ReflexLine12110(ReflexLine):
    def __init__(self, data: ReflexLine12110Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code fournisseur", 13, data.code_seller),
            ("Libellé fournisseur", 30, data.label_seller),
            (
                "Libellé réduit fournisseur",
                15,
                data.label_short_seller,
                {"truncate_silent": True},
            ),
            ("Mot directeur fournisseur", 15, data.director_word_seller),
            ("Code d'usage fournisseur", 13, data.usage_code_seller),
            ("Interlocuteur", 30, data.representative),
            ("Téléphone interlocuteur", 15, data.representative_phone),
            ("Télécopie interlocuteur", 15, data.representative_fax),
            ("Code imputation agrès", 1, data.code_load_carrier_assignment),
            ("Délai douanier", 3, data.customs_delay),
            ("Dépôt physique correspondant", 3, data.linked_physical_location),
            (
                "Top contrôle conditionnement fournisseur",
                1,
                data.flag_packaging_control_seller,
            ),
        ]


class ReflexLine12111Data(ReflexLineDataBase):
    code_interface: str = "12"
    code_rubrique: str = "111"
    code_seller: str
    code_address: str = ""
    name_seller: str
    address: str
    zip_code: str
    city: str
    country: str
    phone_number: str
    fax_number: str
    other_number: str = ""


class ReflexLine12111(ReflexLine):
    def __init__(self, data: ReflexLine12111Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code fournisseur", 13, data.code_seller),
            ("Code adresse", 13, data.address),
            ("Raison sociale", 30, data.name_seller),
            ("address", 30, data.address),
            ("zip code", 30, data.zip_code),
            ("city", 30, data.city),
            ("country", 30, data.country_code),
            ("téléphone", 30, data.phone),
            ("télécopie", 30, data.fax),
            ("autre numéro", 30, data.other_number),
        ]


class ReflexLine32110Data(ReflexLineDataBase):
    code_interface: str = "32"
    code_rubrique: str = "110"
    code_physical_location: str
    code_seller: str
    delivery_note_number: str
    code_shipping_note_type: str
    code_receipt_type: str
    code_receipt_reason: str
    code_purchaser: str
    shipping_note_ref: str
    planned_receipt_date: str
    planned_receipt_time: str = ""
    shipping_note_weight: str = ""
    shipping_note_volume: str = ""
    shipping_note_quantity: str = ""


class ReflexLine32110(ReflexLine):
    def __init__(self, data: ReflexLine32110Data):
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, data.code_interface),
            ("Rubrique", 3, data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code dépôt physique", 3, "023"),
            ("Code fournisseur", 13, self.code_seller),
            ("Numéro de BL", 10, self.delivery_order_number),
            ("Code type d'avis expédition", 3, "010"),
            ("Code type de réception", 3, "010"),
            ("Code motif de réception", 3, "004"),
            ("Code donneur d'ordres", 13, "164"),
            ("Référence livraison avis d'expédition", 20, self.origin),
            ("Date prévue réception", 8, self.delivery_date),
            ("Heure prévue réception", 6),
            ("Poids BL fournisseur", 11),
            ("Volume BL fournisseur", 11),
            ("Quantité transport BL fournisseur", 11),
            ("Code unité de mesure quantité transport", 3, ""),
            ("Délai douanier - Nombre de jours", 3),
            ("Délai douanier - Nombre d'heures minutes (HHMM)", 4),
            ("Code transporteur", 13),
            ("Nom du chauffeur", 20),
            ("Numéro de document transport", 10),
            ("Numéro de plaque minéralogique", 10),
            ("Numéro de plomb 1", 10),
            ("Numéro de plomb 2", 10),
            ("Numéro de plomb 3", 10),
            ("Code atelier", 3),
            ("Code 1 emplacement quai", 4),
            ("Code 2 emplacement quai", 1),
            ("Code 3 emplacement quai", 3),
            ("Code 4 emplacement quai", 2),
            ("Code 5 emplacement quai", 2),
            ("Code famille de stockage", 3),
            ("Code zone de stockage", 6),
            ("Code type emplacement méthode de stockage", 3),
            ("Code méthode de stockage", 6),
            ("Top réception en interception", 1, 0),
            ("Top réception à générer (création réception)", 1, 1),
            ("Top réception à valider", 1, 0),
            ("Top interception à effectuer", 1, 0),
            ("Top générer supports pour la réception", 1, 0),
        ]


class ReflexLine32120(ReflexLine):
    def __init__(
        self,
        sequence,
        code_seller,
        origin,
        delivery_order_number,
        line_sequence,
        product_code,
        qty,
    ):
        self.sequence = sequence
        self.code_seller = code_seller
        self.origin = origin
        self.delivery_order_number = delivery_order_number
        self.line_sequence = line_sequence
        self.product_code = product_code
        self.qty = qty

    def get_values(self):
        return [
            ("N° de séquence", 7, self.sequence),
            ("Code application", 2, "HL"),
            ("Code interface", 2, "32"),
            ("Rubrique", 3, "120"),
            ("Code activité", 3, "164"),
            ("Code dépôt physique", 3, "023"),
            ("Code fournisseur", 13, self.code_seller),
            ("Numéro de BL", 10, self.delivery_order_number),
            ("Numéro de Ligne BL", 6, self.line_sequence),
            ("Référence ligne avis d'expédition", 20, self.origin),
            ("Code article", 16, self.product_code),
            ("Code VL article", 2, "30"),
            ("Référence fournisseur", 20),
            ("Référence de commande", 16),
            ("Code propriétaire", 3, "001"),
            ("Code qualité", 3, "STD"),
            ("Quantité niveau 1", 7, self.qty, {"decimal": 0}),
            ("Quantité niveau 2", 7),
            ("Quantité niveau 3", 7),
            ("Quantité en VL de base", 7),
            ("Quantité en VL de commande", 7),
            ("Poids net", 9),
            ("Poids brut", 9),
            ("Volume", 9),
            ("Prix", 11),
            ("Nombre de VL de sous-conditionnement", 7),
            ("Code type de support", 3),
            ("Code taille emplacement", 3),
        ]


class ReflexLine32129(ReflexLine):
    def __init__(
        self,
        sequence,
        code_seller,
        delivery_order_number,
        comment_line_index,
        comment_family,
        comment,
    ):
        self.sequence = sequence
        self.code_seller = code_seller
        self.delivery_order_number = delivery_order_number
        self.comment_line_index = comment_line_index
        self.comment_family = comment_family
        self.comment = comment

    def get_values(self):
        return [
            ("N° de séquence", 7, self.sequence),
            ("Code application", 2, "HL"),
            ("Code interface", 2, "32"),
            ("Rubrique", 3, "129"),
            ("Code activité", 3, "164"),
            ("Code dépôt physique", 3, "023"),
            ("Code fournisseur", 13, self.code_seller),
            ("Numéro de BL", 10, self.delivery_order_number),
            ("N° ligne commentaire", 3, self.comment_line_index),
            ("Famille de commentaire", 3, self.comment_family),
            ("Commentaire", 70, self.comment),
        ]
