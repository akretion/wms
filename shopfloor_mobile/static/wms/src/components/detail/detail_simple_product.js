/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-simple-product", {
    props: ['product', 'fields', 'shouldSetQuantity'],
    mixins: [ItemDetailMixin],
    data: function() {
        return {
            quantityToSet: 1,
        };
    },
    methods: {
        line_color: function(line) {
            return line.done ? this.utils.colors.color_for('pack_line_done') : undefined;
        },
    },
    template: `
    <v-row>
        <item-detail-card
            :record="product"
            :options="{fields: fields}"
            :card_color="line_color(product)"
        >
            <template v-slot:after_details v-if="shouldSetQuantity">
                <v-container class="pt-0 pb-0">
                    <v-row>
                        <v-col cols="4" offset="4" class="pa-0">
                            <v-text-field
                                label="Quantity to add"
                                type="tel"
                                v-model="quantityToSet"
                                class="ma-0 pa-0"
                                />
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col class="d-flex justify-center pt-0">
                            <v-btn
                                block
                                :color="utils.colors.color_for('screen_step_done')"
                                @click="$emit('addQuantity', [product.barcode, quantityToSet])"
                                >
                                Add
                            </v-btn>
                        </v-col>
                    </v-row>
                </v-container>
            </template>
        </item-detail-card>
    </v-row>
    `,
});
