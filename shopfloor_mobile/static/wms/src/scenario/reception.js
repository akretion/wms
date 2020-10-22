/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Scr :screen_info="screen_info">
            <choosing-reception-contact
                :stateData="offlineListOfContacts"
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
            offlineListOfContacts: {
                contacts: [
                    {
                        contact: "Vendeur 1",
                        receipt_count: 2,
                        code: "V1",
                    },
                    {
                        contact: "Vendeur 2",
                        receipt_count: 10,
                        code: "V2",
                    },
                ],
            },
        };
    },
};

process_registry.add("reception", Reception);

export default Reception;
