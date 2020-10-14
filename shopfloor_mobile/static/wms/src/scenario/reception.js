import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <searchbar
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <receipt-list
                :receipts="offlineListOfReceipts"
                />
        </Screen>
    `,
    data: () => {
        return {
            usage: "reception",
            initial_state_key: "start",
            scan_destination_qty: 0,
            states: {
                start: {},
            },
            offlineListOfReceipts: [
                {
                    reference: "WH/IN/00002",
                    contact: "Vendeur 1",
                },
                {
                    reference: "WH/IN/00003",
                    contact: "Vendeur 2",
                },
            ],
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
