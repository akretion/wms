/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("choosing-reception-contact", {
    props: ["stateData"],
    template: `
        <div>
            <searchbar
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
            />
            <contact-list :contacts="stateData.contacts"/>
        </div>
    `,
});
