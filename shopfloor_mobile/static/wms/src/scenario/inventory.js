import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

const Inventory = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
                <choosing-inventory
                    v-if="state_is('start')"
                    @select-inventory="state.onSelectInventory"
                    :inventories="state.data.inventories"
                    :fields="state.fields"
                />
                <searchbar
                    v-if="state_is('scan_product')"
                    :input_placeholder="scan_placeholder"
                    :refocusInput="true"
                    v-on:found="on_scan"
                />
                <inventory-by-dest
                    v-if="state_is('scan_product')"
                    :inventoryLines="state.data.inventory_lines"
                    :fields="state.fields"
                    :currentLocation="state.data.selected_location"
                    :lastScanned="lastScanned"
                />
        </Screen>
    `,
    methods: {
        screen_title: function() {
            return "Scan stuffs";
        },
    },
    data: function() {
        return {
            usage: "inventory",
            initial_state_key: "start",
            currentLocation: null,
            lastScanned: null,
            states: {
                start: {
                    on_scan: () => {},
                    onSelectInventory: inventory_id => {
                        this.wait_call(this.odoo.call("select_inventory", {
                            inventory_id,
                        }));
                    },
                    enter: () => {
                        if (!this.state_get_data("start").inventories) {
                            this.wait_call(this.odoo.call("list_inventory"));
                        }
                    },
                    fields: [
                        {
                            label: "Locations",
                            path: "locations",
                            renderer: (rec, field) => _.result(rec, field.path).map(loc => loc.name).join(', '),
                        },
                        {
                            label: "Products",
                            path: "products",
                            renderer: (rec, field) => _.result(rec, field.path).length > 0 ? _.result(rec, field.path).map(loc => loc.name).join(', ') : "All",
                        },
                        {
                            label: "Date",
                            path: "date",
                            renderer: (rec, field) => this.utils.display.render_field_date(rec, field),
                        },
                    ],
                },
                scan_product: {
                    on_scan: ({text}) => {
                        this.wait_call(this.odoo.call("select_location", {
                            inventory_id: this.state.data.inventory_id,
                            location_barcode: text,
                        }));
                    },
                    fields: [
                        {
                            label: "Location",
                            path: "location.name",
                        },
                        {
                            label: "Counted",
                            path: "qty",
                        },
                    ],
                },
            },
        };
    },
};

process_registry.add("inventory", Inventory);

export default Inventory;
