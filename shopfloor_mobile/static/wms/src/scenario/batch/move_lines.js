/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("batch-move-line", {
    props: ["moveLines", "fields", "lastScanned", "selectedLocation", "lastPickedLine", "currentLocation"],
    methods: {
        isLastScanned(product) {
            return product && product.barcode === this.lastScanned;
        },
        getLineDest(line) {
            if (line.suggested_package_dest.length > 0) {
                return line.suggested_package_dest[0];
            }
            else if (line.suggested_location_dest.length > 0) {
                return line.suggested_location_dest[0];
            }
        }
    },
    computed: {
        linesBySource: function() {
            const lines = this.moveLines.map((line) => {
                    return {
                        name: line.product.display_name,
                        qty: line.quantity,
                        qtyDone: line.qty_done,
                        done: line.done,
                        source: line.location_src,
                        barcode: line.product.barcode,
                        supplierCode: line.product.supplier_code,
                        id: line.id,
                        dest: this.getLineDest(line),
                    }
            }).filter(line => line.qty > 0 && !(line.done && line.id !==  this.lastPickedLine)).sort((a, b) => a.done ? 1 : -1);

            const selected = lines.find(this.isLastScanned) || {};
            selected.selected = true;

            const sources = lines.map(line => line.source).filter((value, i, array) => {
                return array.findIndex(v => v.id === value.id) === i;
            });

            const sourceWithLines = sources.map(source => {
                return {
                    source,
                    lines: lines.filter(line =>
                        line.source.id === source.id,
                    ).sort((a, b) => !a.selected ? 1 : -1),
                }
            }).filter(source => source.lines.length > 0).sort(
                (a, b) => a.name < b.name ? 1 : -1
            );

            const pivotIndex = sourceWithLines.findIndex(source => source.source.id === this.currentLocation);

            if (pivotIndex !== -1) {
                const removed = sourceWithLines.splice(0, pivotIndex);
                sourceWithLines.push(...removed);
            }

            //(a, b) => a.source.id !== this.selectedLocation ? 1 : -1
            return sourceWithLines;
        },
    },
    template: `
        <v-container class="mb-16">
            <div v-for="source in linesBySource" :key="source.id">
                <item-detail-card
                    :record="source.source"
                    :card_color="utils.colors.color_for(selectedLocation === source.source.id ? 'detail_main_card_selected' : 'detail_main_card')"
                    />
                <detail-simple-product
                    v-for="product in source.lines"
                    :product="product"
                    :fields="fields"
                    :key="product.id"
                    :selected="product.selected"
                    >
                    <template v-slot:actions v-if="product.done">
                        <v-btn
                            @click="$listeners.cancelLine(product.id)"
                            :color="utils.colors.color_for('btn_action_cancel')"
                            >
                            Cancel line
                        </v-btn>
                    </template>
                </detail-simple-product>
            </div>
        </v-container>
    `
});
