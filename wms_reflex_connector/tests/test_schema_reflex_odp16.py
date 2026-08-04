# Copyright 2026 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.wms_reflex_connector.schema_reflex.odp16 import (
    ReflexLine08111,
    ReflexLine08111Data,
    ReflexLine16110,
    ReflexLine16110Data,
    ReflexLine16111,
    ReflexLine16111Data,
    ReflexLine16114,
    ReflexLine16114Data,
    ReflexLine16115,
    ReflexLine16115Data,
    ReflexLine16119,
    ReflexLine16119Data,
    ReflexLine16120,
    ReflexLine16120Data,
    ReflexLine16129,
    ReflexLine16129Data,
)


class TestReflexLine08111(TransactionCase):
    def _make_data(self, **overrides):
        values = {
            "env": self.env,
            "num_sequence": 12,
            "code_activity": "164",
            "dest_partner_code": "DEST001",
            "dest_partner_label": "Akretion Partner",
            "dest_partner_address": "12 rue Exemple",
            "dest_partner_address_more": "Batiment B",
            "postal_code": "69001",
            "city": "Lyon",
            "country_code": "FR",
        }
        values.update(overrides)
        return ReflexLine08111Data(**values)

    def test_get_values_matches_existing_08111_payload_order_widths_and_options(self):
        line = ReflexLine08111(self._make_data())

        self.assertEqual(
            line.get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "08"),
                ("Rubrique", 3, "111"),
                ("Code activité", 3, "164"),
                ("Code destinataire", 13, "DEST001"),
                ("Code adresse", 13, ""),
                (
                    "Raison social",
                    30,
                    "Akretion Partner",
                    {"truncate_silent": True},
                ),
                (
                    "Adresse 1 destinataire",
                    30,
                    "12 rue Exemple",
                    {"truncate_silent": True},
                ),
                (
                    "Adresse 2 destinataire",
                    30,
                    "Batiment B",
                    {"truncate_silent": True},
                ),
                ("Adresse 3 destinataire - CP", 9, "69001"),
                (
                    "Adresse 3 destinataire - Ville",
                    21,
                    "Lyon",
                    {"truncate_silent": True},
                ),
                ("Adresse 4 destinataire", 30, "FR"),
                ("Téléphone destinataire", 15, ""),
                ("Télécopie destinataire", 15, ""),
                ("Autre numéro destinataire", 10, ""),
            ],
        )

    def test_defaults_and_falsey_primary_address_are_serialized(self):
        line = ReflexLine08111(
            self._make_data(
                dest_partner_address=False,
                dest_partner_address_more="",
            )
        )

        values = line.get_values()
        self.assertEqual(values[1], ("Code application", 2, "HL"))
        self.assertEqual(values[2], ("Code interface", 2, "08"))
        self.assertEqual(values[3], ("Rubrique", 3, "111"))
        self.assertEqual(values[8], ("Adresse 1 destinataire", 30, ".", {"truncate_silent": True}))

    def test_explicit_blank_placeholder_fields_can_be_supplied(self):
        line = ReflexLine08111(
            self._make_data(
                address_code="ADDR001",
                dest_partner_phone="0102030405",
                dest_partner_fax="0504030201",
                dest_partner_other_number="ALT001",
            )
        )

        values = line.get_values()
        self.assertEqual(values[6], ("Code adresse", 13, "ADDR001"))
        self.assertEqual(values[13], ("Téléphone destinataire", 15, "0102030405"))
        self.assertEqual(values[14], ("Télécopie destinataire", 15, "0504030201"))
        self.assertEqual(values[15], ("Autre numéro destinataire", 10, "ALT001"))

    def test_render_preserves_legacy_serialized_output_for_default_placeholders(self):
        data = self._make_data()
        rendered = ReflexLine08111(data).render()

        self.assertEqual(len(rendered), 265)
        self.assertIn("HL08111164DEST001", rendered)
        self.assertIn("Akretion Partner", rendered)
        self.assertIn("12 rue Exemple", rendered)
        self.assertIn("Batiment B", rendered)
        self.assertIn("69001", rendered)
        self.assertIn("Lyon", rendered)
        self.assertIn("FR", rendered)


class TestReflexLine16110(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_order_widths_values_and_options(self):
        data = self._make_data(
            ReflexLine16110Data,
            internal_ref=False,
            dest_ref="DEST-REF",
            dest_partner_code="DEST001",
            expected_date="20260804",
            estimated_deliv_date="20260805",
        )

        self.assertEqual(
            ReflexLine16110(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "110"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("Code type de préparation", 3, "010"),
                ("NON UTILISE", 12, ""),
                ("Code destinataire final", 13, "DEST001"),
                ("Référence destinataire final", 20, "DEST-REF"),
                ("Date de livraison demandée", 8, "20260804"),
                ("Heure début livraison demandée", 4, ""),
                ("Heure fin livraison demandée", 4, ""),
                ("Type date de livraison demandée", 3, "010"),
                ("Date prévue de livraison finale", 8, ""),
                ("Heure début livraison finale", 4, ""),
                ("Heure fin livraison finale", 4, ""),
                ("Top livraison globalisée", 1, ""),
                ("Code circuit de prélèvement", 10, "001"),
                ("Date de lancement", 8, 0),
                ("Code lancement", 3, ""),
                ("Date de chargement", 8, 0),
                ("Code chargement", 6, ""),
                ("Emplacement 1 de mise à disposition", 4, ""),
                ("Emplacement 2 de mise à disposition", 1, ""),
                ("Emplacement 3 de mise à disposition", 3, ""),
                ("Emplacement 4 de mise à disposition", 2, ""),
                ("Emplacement 5 de mise à disposition", 2, ""),
                ("Top destinataire intermédiaire", 1, "0"),
                ("Code destinataire intermédiaire", 13, ""),
                ("Référence destinataire intermédiaire", 20, ""),
                ("Date de livraison intermédiaire", 8, ""),
                ("Heure début livraison intermédiaire", 4, ""),
                ("Heure fin livraison intermédiaire", 4, ""),
                ("Top édition bordereau d'éclatement", 1, ""),
                ("Top édition des BL finaux", 1, ""),
                ("Top ODP protégé", 1, "0"),
                ("Top génération automatique", 1, "0"),
                ("Code qualité transport", 3, ""),
                ("Top sortie de stock à la validation de préparation", 1, ""),
                ("Code famille de préparation", 3, ""),
                ("Référence de réservation", 20, ""),
            ],
        )


class TestReflexLine16111(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_order_widths_values_and_options(self):
        data = self._make_data(ReflexLine16111Data, internal_ref=False)

        self.assertEqual(
            ReflexLine16111(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "111"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("Top RV pris destinataire final", 1, "0"),
                ("Date RV destinataire final - Siècle", 2, 0),
                ("Date RV destinataire final - Année", 2, 0),
                ("Date RV destinataire final - Mois", 2, 0),
                ("Date RV destinataire final - Jour", 2, 0),
                ("Heure début RV destinataire final", 4, 0),
                ("Heure fin RV destinataire final", 4, 0),
                ("Top RV pris destinataire intermédiaire", 1, "0"),
                ("Date RV destinataire intermédiaire - Siècle", 2, 0),
                ("Date RV destinataire intermédiaire - Année", 2, 0),
                ("Date RV destinataire intermédiaire - Mois", 2, 0),
                ("Date RV destinataire intermédiaire - Jour", 2, 0),
                ("Heure début RV destinataire intermédiaire", 4, 0),
                ("Heure fin RV destinataire intermédiaire", 4, 0),
                ("Motif ordre de préparation", 3, ""),
                ("Date de préparation prévue - Siècle", 2, 0),
                ("Date de préparation prévue - Année", 2, 0),
                ("Date de préparation prévue - Mois", 2, 0),
                ("Date de préparation prévue - Jour", 2, 0),
                ("Regroupement chargement", 10, ""),
                ("Regroupement expédition", 13, ""),
                ("Date de fin de réservation - Siècle", 2, 0),
                ("Date de fin de réservation - Année", 2, 0),
                ("Date de fin de réservation - Mois", 2, 0),
                ("Date de fin de réservation - Jour", 2, 0),
                ("Heure de fin de réservation", 4, 0),
            ],
        )


class TestReflexLine16114(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_and_data_normalization(self):
        data = self._make_data(
            ReflexLine16114Data,
            internal_ref=False,
            civil_status_code=2,
            firstname=False,
            lastname=False,
            email=False,
        )

        self.assertEqual(data.internal_ref, "")
        self.assertEqual(data.firstname, ".")
        self.assertEqual(data.lastname, ".")
        self.assertEqual(data.email, "")
        self.assertEqual(
            ReflexLine16114(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "114"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("Code type de contact", 3, "010"),
                ("Code civilité", 1, 2),
                ("Prénom du contact", 35, "."),
                ("Nom du contact", 35, "."),
                ("Code type d'adresse 1", 3, "010"),
                ("Adresse 1 du contact", 140, ""),
            ],
        )


class TestReflexLine16115(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_and_data_normalization(self):
        data = self._make_data(
            ReflexLine16115Data,
            internal_ref=False,
            partner_mobile=False,
            partner_phone=False,
        )

        self.assertEqual(data.partner_mobile, "")
        self.assertEqual(data.partner_phone, "")
        self.assertEqual(
            ReflexLine16115(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "115"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("Code type de contact", 3, "010"),
                ("Numéro de téléphone mobile", 20, ""),
                ("Numéro de téléphone fixe", 20, ""),
                ("Numéro de fax", 20),
            ],
        )


class TestReflexLine16119(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_order_widths_values_and_options(self):
        data = self._make_data(
            ReflexLine16119Data,
            internal_ref=False,
            comment_line_index="002",
            comment_family="FAM",
            comment="Handle with care",
        )

        self.assertEqual(
            ReflexLine16119(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "119"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("N° ligne commentaire", 3, "002"),
                ("Famille de commentaire", 3, "FAM"),
                ("Commentaire", 70, "Handle with care"),
            ],
        )


class TestReflexLine16120(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_payload_decimal_options_and_blank_types(self):
        data = self._make_data(
            ReflexLine16120Data,
            internal_ref=False,
            line_index=7,
            product_code="ART001",
            qty=3,
        )

        self.assertEqual(
            ReflexLine16120(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "120"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("N° ligne référence donneur d'ordres", 7, 7),
                ("Code article", 16, "ART001"),
                ("Code VL article", 2, "10"),
                ("Référence conditionnement destinataire", 20, ""),
                ("Référence de commande de la VL", 16, ""),
                ("Quantité niveau 1 à préparer", 7, 3, {"decimal": 0}),
                ("Quantité niveau 2 à préparer", 7, ""),
                ("Quantité niveau 3 à préparer", 7, ""),
                (
                    "Quantité à préparer en VL de base (ou en VL de commande)",
                    7,
                    3,
                    {"decimal": 0},
                ),
                ("Poids net à préparer", 9, ""),
                ("Poids brut à préparer", 9, ""),
                ("Volume à préparer", 9, ""),
                ("Code propriétaire à préparer", 3, ""),
                ("Code qualité à préparer", 3, "STD"),
                ("Top infos commande saisies", 1, "0"),
                ("Quantité niveau 1 commandée", 7, 3),
                ("Quantité niveau 2 commandée", 7, ""),
                ("Quantité niveau 3 commandée", 7, ""),
                ("Quantité commandée en VL de base ou en VL de commande", 7, ""),
                ("Poids net commandé", 9, ""),
                ("Poids brut commandé", 9, ""),
                ("Volume commandé", 9, ""),
                ("Code propriétaire commandé", 3, ""),
                ("Code qualité commandée", 3, "STD"),
                ("Top réservation stock", 1, 0),
                ("Code priorité de service", 1, ""),
                ("Top délai mini date ordo forcée", 1, 0),
                ("Nb jours mini date ordo forcée", 3, 0),
                ("Top chaînage possible", 1, 0),
                ("Top substitution possible", 1, 0),
                ("Lot 1", 20, ""),
                ("Top quantité VL de base", 1, 0),
                ("Top VL indifférente", 1, 0),
            ],
        )


class TestReflexLine16129(TransactionCase):
    def _make_data(self, data_class, **overrides):
        values = {"env": self.env, "num_sequence": 12, "code_activity": "164"}
        values.update(overrides)
        return data_class(**values)

    def test_get_values_preserves_legacy_default_comment_fields(self):
        data = self._make_data(
            ReflexLine16129Data,
            internal_ref=False,
            line_index=7,
        )

        self.assertEqual(data.comment_line_number, "001")
        self.assertEqual(data.comment_family, "")
        self.assertEqual(data.comment, "")
        self.assertEqual(
            ReflexLine16129(data).get_values(),
            [
                ("N° de séquence", 7, 12),
                ("Code application", 2, "HL"),
                ("Code interface", 2, "16"),
                ("Rubrique", 3, "129"),
                ("Code activité", 3, "164"),
                ("Code dépôt physique", 3, "023"),
                ("Code donneur d'ordres", 13, "164"),
                ("Référence donneur d'ordres", 20, ""),
                ("N° ligne référence donneur d'ordres", 7, 7),
                ("N° de ligne commentaire", 3, "001"),
                ("Famille de commentaire", 3, ""),
                ("Commentaire", 70, ""),
            ],
        )
