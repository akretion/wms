/**
 * Copyright 2020 Akretion SA (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("batch-move-line", {
    props: ["batch"],
    computed: {
        lines: function() {
            const lines = this.pickings.flatMap((picking) => {
                picking.move_lines.map((line) => {
                    return {
                        name: line.product.display_name,
                        qty: line.quantity,
                        qtyDone: line.qty_done,
                        source: line.location_src,
                    }
                });
            });

            const linesBySource = {};

            lines.forEach((line) => {
                linesBySource[line.source] = [
                    line,
                    ...linesBySource[line.source] || []
                ];
            });
        },
    },
    template: `
        <v-container class="mb-16">
            <batch-picking-line-detail
                v-if="state_in(['start_line', 'scan_destination', 'change_pack_lot', 'stock_issue'])"
                :line="state.data"
                :article-scanned="state_is('scan_destination')"
                :show-qty-picker="state_is('scan_destination')"
                />
        </v-container>
    `
};
