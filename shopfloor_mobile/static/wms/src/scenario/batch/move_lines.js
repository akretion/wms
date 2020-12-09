/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("batch-move-line", {
    props: ["batch", "fields", "lastScanned"],
    methods: {
        isLastScanned(product) {
            return product && product.barcode === this.lastScanned;
        },
    },
    computed: {
        linesBySource: function() {
            const lines = this.batch.pickings.flatMap((picking) => {
                return picking.move_lines.map((line) => {
                    return {
                        name: line.product.display_name,
                        qty: line.quantity,
                        qtyDone: line.qty_done,
                        done: line.done,
                        source: line.location_src,
                        barcode: line.product.barcode,
                        supplierCode: line.product.supplier_code,
                    }
                });
            });

            const sources = lines.map(line => line.source).filter((value, i, array) => {
                return array.findIndex(v => v.id = value.id) === i;
            });

            const sourceWithLines = sources.map(source => {
                return {
                    source,
                    lines: lines.filter(line =>
                        line.source.id === source.id,
                    ),
                }
            });

            return sourceWithLines;
        },
    },
    template: `
        <v-container class="mb-16">
            <div v-for="source in linesBySource">
                <item-detail-card
                    :record="source.source"
                    :card_color="utils.colors.color_for('detail_main_card')"
                    />
                <detail-simple-product
                    v-for="product in source.lines"
                    :product="product"
                    :fields="fields"
                    :key="product.id"
                    :selected="isLastScanned(product)"
                    v-on:addQuantity="$listeners.addQuantity"
                    />
            </div>
        </v-container>
    `
});
