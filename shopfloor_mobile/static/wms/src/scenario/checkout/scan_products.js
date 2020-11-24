/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("checkout-scan-products", {
    props: ["packing", "products", "fields","lastScanned"],
    methods: {
        shouldSetQuantity(product) {
            return product && product.barcode === this.lastScanned;
        },
    },
    computed: {
        all_lines_done: function() {
            return this.products.every(prod => prod.done);
        },
        formatedProducts: function() {
            return this.products.map(
                    prod => ({
                        id: prod.product.id,
                        name: prod.product.name,
                        qty: prod.quantity,
                        qtyDone: prod.qty_done,
                        done: prod.done,
                        barcode: prod.product.barcode,
                        supplierCode: prod.product.supplier_code,
                    }),
                );
        },
    },
    template: `
    <v-container class="mb-16">
        <detail-picking
            :record="packing"
        />
        <detail-simple-product
            v-for="product in formatedProducts"
            :product="product"
            :fields="fields"
            :key="product.id"
            :shouldSetQuantity="shouldSetQuantity(product)"
            v-on:addQuantity="$listeners.addQuantity"
            />
        <div style="position: fixed; bottom: 0; right: 12px;width: 100%">
            <v-row>
                <v-col
                    class="d-flex justify-end"
                    >
                    <v-btn
                        v-if="all_lines_done"
                        x-large
                        class="justify-end"
                        @click="$emit('shippedFinished')"
                        :color="utils.colors.color_for('screen_step_done')">
                        Package done
                    </v-btn>
                    <v-btn
                        v-if="!all_lines_done"
                        x-large
                        @click="$emit('shippedUnfinished')"
                        :color="utils.colors.color_for('secondary')">
                        Ship unfinished
                    </v-btn>
                </v-col>
            </v-row>
        </div>
    </v-container>
`,
});
