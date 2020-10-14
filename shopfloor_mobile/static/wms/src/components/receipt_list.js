/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("receipt-list", {
    props: ["receipts"],
    template: `
    <div>
        <v-row dense>
            <receipt-detail v-for="receipt in receipts" :receipt="receipt" />
        </v-row>
    </div>
    `,
});
