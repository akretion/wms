/**
 * Copyright 2024 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";
import {process_registry} from "/shopfloor_mobile_base/static/wms/src/services/process_registry.js";

export var MRPProdStatesMixin = {
    data: function () {
        return {
            states: {
                // Generic state for when to start w/ scanning a pack or loc
                start: {
                    display_info: {
                        title: "Start by scanning an manufacturing order",
                        scan_placeholder: "Scan MO",
                    },
                    on_scan: (scanned) => {
                        const data = this.state.data;
                        this.wait_call(
                            this.odoo.call("start", {
                                barcode: scanned.text,
                                confirmation: data.confirmation_required || "",
                            })
                        );
                    },
                },
                mark_as_done: {
                    display_info: {
                        title: "Mark as done",
                        show_cancel_button: true,
                    },
                    on_confirm: () => {
                        const data = this.state.data;
                        this.wait_call(
                            this.odoo.call("action_confirm", {
                                barcode: scanned.text,
                                confirmation: data.confirmation_required || "",
                            })
                        );
                    },
                },
                scan_location: {
                    display_info: {
                        title: "Set a location",
                        scan_placeholder: "Scan location",
                        show_cancel_button: true,
                    },
                    on_scan: (scanned, confirmation = false) => {
                        const data = this.state.data;
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("validate", {
                                mrp_production_id: data.id,
                                location_barcode: scanned.text,
                                confirmation:
                                    confirmation || data.confirmation_required || "",
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(this.odoo.call("cancel", {}));
                    },
                },
            },
        };
    },
};

// TODO: consider replacing the dynamic "autofocus" in the searchbar by an event.
// At the moment, we need autofocus to be disabled if there's a user popup.
const MRPProduction = {
    mixins: [ScenarioBaseMixin, MRPProdStatesMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state_is(initial_state_key)"
                v-on:found="on_scan"
                :autofocus="!screen_info.user_popup"
                :input_placeholder="search_input_placeholder"
            ></searchbar>
            <searchbar
                v-if="state_is('scan_location')"
                v-on:found="on_scan"
                :autofocus="!screen_info.user_popup"
                :input_placeholder="search_input_placeholder"
                :input_data_type="'location'"
            ></searchbar>

            <div v-if="state_is('scan_location')">
                <item-detail-card
                    :key="make_state_component_key(['mrp_production', state.data.id])"
                    :record="state.data"
                    :card_color="utils.colors.color_for('screen_step_done')"
                >
                    <template v-slot:after_details>
                        <v-card-text class="details pt-0">
                            <div class="field-detail">
                                {{ state.data.product.display_name}}
                            </div>
                        </v-card-text>
                        <v-card-subtitle>
                            <span class="font-weight-bold">Quantity:</span>
                            <span>
                            {{ state.data.qty_to_produce }}
                            </span>
                        </v-card-subtitle>
                    </template>
                </item-detail-card>

                <item-detail-card
                    :key="make_state_component_key(['destination', state.data.id])"
                    :record="state.data"
                    :options="{main: true, key_title: 'location_dest.name', title_action_field:  {action_val_path: 'location_dest.barcode'}}"
                    :card_color="utils.colors.color_for('screen_step_todo')"
                />

            </div>
            <div v-if="_.result(state, 'data.scan_location')">


            </div>

            <div v-if="state_is('confirm_done')">
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action action="todo" @click="state.on_confirm">Confirm</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-back />
                        </v-col>
                    </v-row>
                </div>
            </div>

            <last-operation v-if="state_is('show_completion_info')" v-on:confirm="state.on_confirm"></last-operation>
            <cancel-button v-on:cancel="on_cancel" v-if="show_cancel_button"></cancel-button>
        </Screen>
    `,
    data: function () {
        return {
            usage: "mrp_production",
            show_reset_button: true,
            initial_state_key: "start",
            states: {
                show_completion_info: {
                    on_confirm: () => {
                        // TODO: turn the cone?
                        this.state_to("start");
                    },
                },
            },
        };
    },
    methods: {
        _get_pack_weight: function () {
            let weight = this.state.data.weight;
            let uom = this.state.data.weight_uom;
            if (!weight) {
                weight = this.state.data.estimated_weight_kg;
                uom = "kg";
            }
            return weight.toFixed(3) + " " + uom;
        },
    },
};
process_registry.add("mrp_production", MRPProduction);

export default MRPProduction;
