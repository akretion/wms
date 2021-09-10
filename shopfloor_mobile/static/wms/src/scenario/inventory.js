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
        </Screen>
    `,
    methods: {
        screen_title: function() {
            return "Scan stuffs";
        },
    },
    data: function() {
        // TODO: add a title to each screen
        return {
            usage: "inventory",
            initial_state_key: "start",
            currentLocation: null,
            lastPickedLine: null,
            states: {
                start: {
                    on_scan: () => {},
                    onSelectInventory: inventory_id => {
                        this.wait_call(this.odoo.call("select_inventory"), {
                            inventory_id,
                        });
                    },
                    enter: () => {
                        if (!this.state_get_data("start").inventories) {
                            this.wait_call(this.odoo.call("list_inventory"));
                        }
                    },
                    fields: [
                    ],
                },
            },
        };
    },
};

process_registry.add("inventory", Inventory);

export default Inventory;
