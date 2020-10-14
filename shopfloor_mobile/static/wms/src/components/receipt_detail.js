/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("receipt-detail", {
    props: ["receipt"],
    template: `
        <v-col
            :key="receipt.reference"
            :cols="12"
            >
            <v-card>
                <v-card-title>{{receipt.reference}}</v-card-title>
                <v-card-subtitle>Fournisseur: {{receipt.contact}}</v-card-title>
            </v-card>
        </v-col>
    `,
});
