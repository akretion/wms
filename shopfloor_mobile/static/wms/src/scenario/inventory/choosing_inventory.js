/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-inventory", {
    props: ["inventories", "fields"],
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
                :refocusInput="true"
                v-on:found="(scanned) => $emit('select-inventory',scanned.text)"
            />
            <item-detail-card
                v-for="inventory in inventories"
                :record="inventory"
                :options="{fields: fields, full_detail: true, on_click_action: () => $emit('select-inventory', inventory.id)}"
                />
            <div
                v-if="!inventories || inventories.length === 0"
                >
                There is no inventories to process
            </div>
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan a inventory id",
    }),
});
