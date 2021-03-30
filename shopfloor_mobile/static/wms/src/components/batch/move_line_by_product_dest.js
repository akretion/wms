/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("batch-product-by-dest", {
    props: [
        "moveLines",
        "fields",
        "lastScanned",
        "selectedLocation",
        "lastPickedLines",
        "currentLocation",
    ],
    methods: {
        isLastScanned(product) {
            return (
                this.lastScanned &&
                product &&
                this.lastScanned.includes(product.barcode)
            );
        },
    },
    computed: {
        productByDest: function() {
            const lines = this.moveLines
                .map(line => {
                    return {
                        name: line.product.display_name,
                        qty: line.quantity,
                        qtyDone: line.qty_done,
                        done: line.done,
                        source: line.location_src,
                        barcode: line.product.barcode,
                        supplierCode: line.product.supplier_code,
                        id: line.id,
                        dest: line.location_dest,
                        productId: line.product.id,
                    };
                })
                .filter(
                    line =>
                        line.qty > 0 &&
                        !(line.done && this.lastPickedLines.indexOf(line.id) === -1)
                )
                .sort((a, b) => (a.done ? 1 : -1));

            const linesByProduct = Object.values(
                lines.reduce((acc, line) => {
                    (acc["" + line.productId + line.done] =
                        acc["" + line.productId + line.done] || []).push(line);
                    return acc;
                }, {})
            ).map(prodLines => {
                return prodLines.reduce(
                    (acc, lineProd) => ({
                        name: lineProd.name,
                        qty: acc.qty + lineProd.qty,
                        qtyDone: acc.qtyDone + lineProd.qtyDone,
                        done: acc.done && lineProd.done,
                        barcode: lineProd.barcode,
                        supplierCode: lineProd.supplierCode,
                        id: [lineProd.id, ...acc.id],
                        dest: lineProd.dest,
                        productId: lineProd.productId,
                    }),
                    {
                        qty: 0,
                        qtyDone: 0,
                        done: true,
                        id: [],
                    }
                );
            });

            const selected = linesByProduct.find(this.isLastScanned) || {};
            selected.selected = true;

            const dests = linesByProduct
                .map(line => line.dest)
                .filter((value, i, array) => {
                    return array.findIndex(v => v.id === value.id) === i;
                });

            const destWithProducts = dests
                .map(dest => {
                    return {
                        dest,
                        lines: linesByProduct
                            .filter(line => line.dest.id === dest.id)
                            .sort((a, b) => (!a.selected ? 1 : -1)),
                    };
                })
                .filter(dest => dest.lines.length > 0)
                .sort((a, b) => (a.name < b.name ? 1 : -1));

            const pivotIndex = destWithProducts.findIndex(
                dest => dest.dest.id === this.currentLocation
            );

            if (pivotIndex !== -1) {
                const removed = destWithProducts.splice(0, pivotIndex);
                destWithProducts.push(...removed);
            }

            //(a, b) => a.source.id !== this.selectedLocation ? 1 : -1
            return destWithProducts;
        },
    },
    template: `
        <v-container class="mb-16">
            <div v-for="dest in productByDest" :key="dest.id">
                <item-detail-card
                    :record="dest.dest"
                    :card_color="utils.colors.color_for(selectedLocation === dest.dest.id ? 'detail_main_card_selected' : 'detail_main_card')"
                    />
                <detail-simple-product
                    v-for="product in dest.lines"
                    :product="product"
                    :fields="fields"
                    :key="product.id"
                    :selected="product.selected"
                    >
                    <template v-slot:actions>
                        <line-actions-popup
                            @action="$listeners.action"
                            :line="product"
                            :actions="[
                                {name: 'Declare stock out', event_name: 'actionStockOut', move_line_id: product.id, condition: !product.done},
                                {name: 'Change pack or lot', event_name: 'actionChangePack', condition: !product.done},
                                {name: 'Cancel line', event_name: 'cancelLine', move_line_id: product.id, condition: product.done},
                            ]"
                            xxxkey="make_state_component_key(['line-actions', product.id])"
                            xxv-on:action="state.on_action"
                            />
                    </template>
                </detail-simple-product>
            </div>
        </v-container>
    `,
});
