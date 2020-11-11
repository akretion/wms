/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("checkout-scan-products", {
    props: ["products", "fields"],
    data: function() {
        console.log(this.fields)
        return {
            formatedProducts: this.products.map(
                prod => ({
                    id: prod.product.id,
                    name: prod.product.name,
                    qty: prod.quantity,
                    qtyDone: prod.qty_done,
                }),
            ),
        };
    },
    template: `
    <div>
        <item-detail-card
            v-for="product in formatedProducts"
            :record="product"
            :key="product.id"
            :options="{fields: fields}"
        />
    </div>
`,
});
