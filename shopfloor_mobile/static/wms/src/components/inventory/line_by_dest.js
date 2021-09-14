/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("inventory-by-dest", {
    props: [
        "inventoryLines",
        "fields",
        "lastScanned",
        "currentLocation",
        "productScanned",
    ],
    methods: {
        isLastScanned(product) {
            return (
                product &&
                ((product.barcode !== null && product.barcode === this.lastScanned) ||
                    (product.barcodes.length > 0 && product.barcodes.includes(this.lastScanned)))
            );
        },
    },
    computed: {
        linesByLocation: function() {
            const lines = this.inventoryLines
                .map(line => {
                    return {
                        name: line.product.display_name,
                        id: line.id,
                        location: line.location,
                        barcodes: line.product.barcodes,
                        qty: line.product_qty,
                    };
                })
                .sort((a, b) => (a.done ? 1 : -1));

            const selected = lines.find(this.isLastScanned) || {};
            selected.selected = true;

            const locations = lines
                .map(line => line.location)
                .filter((value, i, array) => {
                    return array.findIndex(v => v.id === value.id) === i;
                });

            const locationWithLines = locations
                .map(location => {
                    return {
                        location,
                        lines: lines
                            .filter(line => line.location.id === location.id)
                            .sort((a, b) => (!a.selected ? 1 : -1)),
                    };
                })
                .filter(location => location.lines.length > 0)
                .sort((a, b) => (a.name < b.name ? 1 : -1));

            const pivotIndex = locationWithLines.findIndex(
                location => location.location.id === this.currentLocation
            );

            if (pivotIndex !== -1) {
                const removed = locationWithLines.splice(0, pivotIndex);
                locationWithLines.push(...removed);
            }

            return locationWithLines;
        },
    },
    template: `
        <v-container class="mb-16">
            <div v-for="location in linesByLocation" :key="location.id">
                <item-detail-card
                    :record="location.location"
                    :card_color="utils.colors.color_for(currentLocation === location.location.id ? 'detail_main_card_selected' : 'detail_main_card')"
                    />
                <detail-simple-product
                    v-if="productScanned.includes(product.id)"
                    v-for="product in location.lines"
                    :product="product"
                    :fields="fields"
                    :key="product.id"
                    :selected="product.selected"
                    >
                </detail-simple-product>
            </div>
        </v-container>
    `,
});
