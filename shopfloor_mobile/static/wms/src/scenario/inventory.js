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
                    :productScanned="productScanned"
                />
        </Screen>
    `,
    methods: {
        screen_title: function() {
            return "Scan stuffs";
        },
        getLastScannedLine: function() {
            return this.state.data.inventory_lines.find(line =>
                line.product.barcode == this.lastScanned ||
                line.product.barcodes.map(b => b.name).includes(
                    this.lastScanned
                ));

        }
    },
    computed: {
        currentDestLocation: function() {
            return this.state.data.selected_location;
        },
        productScanned: function() {
            return this.state.data.product_scanned_list;
        },
    },
    data: function() {
        return {
            usage: "inventory",
            initial_state_key: "start",
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
                        const intInText =
                            "" + text == parseInt(text, 10) &&
                            parseInt(text, 10);

                        if (!this.currentDestLocation) {
                            this.wait_call(this.odoo.call("select_location", {
                                inventory_id: this.state.data.inventory_id,
                                location_barcode: text,
                            }));
                        }
                        else {
                            if (this.state.data.inventory_lines.find(line =>
                                line.location.barcode === text
                            )) {
                                this.wait_call(this.odoo.call("select_location", {
                                    inventory_id: this.state.data.inventory_id,
                                    location_barcode: text,
                                }))
                            }
                            else {
                                if (this.lastScanned && !isNaN(intInText) && intInText >= 0 &&
                                    this.getLastScannedLine()
                                    ) {
                                    const line = this.getLastScannedLine();
                                    this.wait_call(this.odoo.call("set_quantity",
                                        {
                                            inventory_id: this.state.data.inventory_id,
                                            location_id: this.currentDestLocation,
                                            product_id: line.product.id,
                                            qty: intInText,
                                            product_scanned_list_id: this.productScanned,
                                        }
                                    ));
                                }
                                else {
                                    this.wait_call(this.odoo.call("scan_product",
                                        {
                                            inventory_id: this.state.data.inventory_id,
                                            location_id: this.currentDestLocation,
                                            barcode: text,
                                            product_scanned_list_id: this.productScanned,
                                        }
                                    ));
                                    this.lastScanned = text;
                                }
                            }
                        }
                    },
                    fields: [
                        {
                            label: "Counted",
                            path: "qty",
                            klass: "title",
                        },
                    ],
                },
            },
        };
    },
};

process_registry.add("inventory", Inventory);

export default Inventory;
