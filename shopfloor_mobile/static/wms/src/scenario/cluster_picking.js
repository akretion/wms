import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

const ClusterPicking = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <searchbar
                v-if="state.on_scan"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                :refocusInput="true"
                />
            <get-work
                v-if="state_is('start')"
                v-on:get_work="state.on_get_work"
                v-on:manual_selection="state.on_manual_selection"
                />
            <batch-picking-detail
                v-if="state_is('confirm_start')"
                :record="state.data"
                v-on:confirm="state.on_confirm"
                v-on:cancel="state.on_cancel"
                />
            <batch-picking-line-detail
                v-if="state_in(['start_line', 'scan_destination', 'change_pack_lot', 'stock_issue'])"
                :line="state.data"
                :article-scanned="state_is('scan_destination')"
                :show-qty-picker="state_is('scan_destination')"
                />
            <batch-move-line
                v-if="state_is('scan_products')"
                :batch="state.data"
                :fields="state.fields"
                :lastScanned="lastScanned"
                :selectedLocation="selectedLocation"
                @cancelLine="state.cancelLine"
                />
            <batch-picking-line-actions
                v-if="state_is('start_line')"
                v-on:action="state.on_action"
                :line="state_get_data('start_line')"
                />
            <div v-if="state_is('scan_destination')">
                <div class="button-list button-vertical-list full mt-10">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn @click="state.on_action_full_bin">
                                Full bin
                            </v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>
            <stock-zero-check
                v-if="state_is('zero_check')"
                v-on:action="state.on_action"
                />

            <line-stock-out
                v-if="state_is('stock_issue')"
                v-on:confirm_stock_issue="state.on_confirm_stock_issue"
                />

            <div v-if="state_is('manual_selection')">
                <manual-select
                    v-on:select="state.on_select"
                    v-on:back="state.on_back"
                    :records="state.data.records"
                    :list_item_fields="manual_select_picking_fields"
                    />
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="default" @click="state.on_back">Back</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div class="unload-all" v-if="state_is('unload_all')">
                <v-card class="main">
                    <v-card-title>
                        <div class="main-info">
                            <div class="destination">
                                <span class="label">Destination:</span>
                                {{ state.data.location_dest.name }}
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn color="primary" @click="$emit('action', 'action_split')">Split [TODO]</v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_in(['unload_all', 'change_pack_lot'])">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>

        </Screen>
    `,
    computed: {
        manual_select_picking_fields: function() {
            return [
                {path: "picking_count", label: "Operations"},
                {path: "move_line_count", label: "Lines"},
            ];
        },
    },
    methods: {
        screen_title: function() {
            if (_.isEmpty(this.current_batch()) || this.state_is("confirm_start"))
                return this.menu_item().name;
            let title = this.current_batch().name;
            const picking = this.current_picking();
            if (picking) {
                title += " > " + picking.name;
            }
            return title;
        },
        current_batch: function() {
            return this.state_get_data("confirm_start");
        },
        current_picking: function() {
            const data = this.state_get_data("start_line") || {};
            if (!data.picking) {
                return null;
            }
            return data.picking;
        },
        current_doc: function() {
            const picking = this.current_picking();
            if (!picking) {
                return {};
            }
            return {
                record: picking,
                identifier: picking.name,
            };
        },
        action_full_bin: function() {
            this.wait_call(
                this.odoo.call("prepare_unload", {
                    picking_batch_id: this.current_batch().id,
                })
            );
        },
        find_move_line: function(pickings, barcode, filter=() => true) {
            let move_line;

            pickings.forEach(picking =>
                picking.move_lines.filter(filter).forEach(line => {
                    if (line.product.barcode === barcode) {
                        move_line = move_line !== undefined ? move_line : line;
                    }
                })
            );

            return move_line || {};
        },
        find_src_location: function(pickings, barcode) {
            let location_src = "";

            pickings.forEach(picking =>
                picking.move_lines.forEach(line => {
                    if (line.location_src.barcode === barcode) {
                        location_src = line.location_src.id;
                    }
                })
            );

            return location_src;
        }
    },
    data: function() {
        // TODO: add a title to each screen
        return {
            usage: "cluster_picking",
            initial_state_key: "start",
            scan_destination_qty: 0,
            states: {
                start: {
                    on_get_work: evt => {
                        this.wait_call(this.odoo.call("find_batch"));
                    },
                    on_manual_selection: evt => {
                        this.wait_call(this.odoo.call("list_batch"));
                    },
                },
                manual_selection: {
                    on_back: () => {
                        this.state_to("start");
                        this.reset_notification();
                    },
                    on_select: selected => {
                        this.wait_call(
                            this.odoo.call("select", {
                                picking_batch_id: selected.id,
                            })
                        );
                    },
                    display_info: {
                        title: "Select a batch and start",
                    },
                },
                confirm_start: {
                    on_confirm: () => {
                        this.wait_call(
                            this.odoo.call("confirm_start", {
                                picking_batch_id: this.current_batch().id,
                            })
                        );
                    },
                    on_cancel: () => {
                        const self = this;
                        this.wait_call(
                            this.odoo.call("unassign", {
                                picking_batch_id: this.current_batch().id,
                            })
                        ).then(function() {
                            self.state_reset_data_all();
                        });
                    },
                },
                scan_products: {
                    cancelLine: (move_line_id) => {
                        this.wait_call(
                            this.odoo.call("cancel_line", {
                                move_line_id,
                                picking_batch_id: this.state.data.id,
                            })
                        );
                    },
                    on_scan: scanned => {
                        const intInText = parseInt(scanned.text);
                        let move_line = this.find_move_line(
                            this.state.data.pickings,
                            scanned.text,
                            line => !line.done);
                        let last_move_line = this.find_move_line(
                            this.state.data.pickings,
                            this.lastScanned,
                            line => !line.done);

                        if (!isNaN(intInText) && intInText === 0) {
                            this.wait_call(
                                this.odoo.call("set_quantity_scan_and_pack", {
                                    barcode: this.lastScanned,
                                    picking_batch_id: this.state.data.id,
                                    move_line_id: last_move_line.id,
                                    qty: intInText,
                                })
                            );

                            this.lastScanned = null;
                        }
                        else if (!isNaN(intInText) && intInText > 0 && intInText < 10000 && this.lastScanned) {
                            // scanning quantity
                            if (last_move_line.id) {
                                    this.wait_call(
                                        this.odoo.call("set_quantity_scan_and_pack", {
                                            barcode: this.lastScanned,
                                            picking_batch_id: this.state.data.id,
                                            move_line_id: last_move_line.id,
                                            qty: intInText,
                                        })
                                    );
                            }
                            else {
                                this.set_message({
                                    body: "You can't set quantity for an already pick product",
                                    message_type: "error"
                                });
                            }
                        }
                        else {
                            //scanning barcode
                            if (!move_line.id && !last_move_line.id) {
                                // scanning barcode that does not match with a move_line
                                // and without a previously selected product
                                // this should try to select a location
                                return this.selectedLocation = this.find_src_location(
                                    this.state.data.pickings,
                                    scanned.text,
                                );
                            }
                            if (!move_line.id && last_move_line.id) {
                                // scanning barcode with previous product selection and the barcode
                                // doesn't match a product in the picking
                                // this correspond to scanning a potential location or bin package
                                this.lastScanned = null;

                                return this.wait_call(
                                    this.odoo.call("scan_location_scan_and_pack", {
                                        barcode: scanned.text,
                                        move_line_id: last_move_line.id,
                                        picking_batch_id: this.state.data.id,
                                        qty: last_move_line.qty_done,
                                    })
                                );
                            }
                            else if (move_line.id) {
                                // this is the user scanning a product
                                // we check first if this is the same product as last picked if it exists
                                // in both these cases we increment the qty done for the move_line
                                if (last_move_line.id === move_line.id || !last_move_line.id) {
                                    this.wait_call(
                                        this.odoo.call("scan_product_scan_and_pack", {
                                            barcode: scanned.text,
                                            move_line_id: move_line.id,
                                            picking_batch_id: this.state.data.id,
                                            qty: 1,
                                        })
                                    );

                                    this.lastScanned = scanned.text;
                                }
                                else {
                                    //If the user is trying to scan a new product without unselecting or
                                    //placing the product previously selected product we warn him that's not possible
                                    //they must scan a location or unselect first
                                    this.set_message({
                                        body: "You must scan a destination for the current products, or unselect it",
                                        message_type: "error"
                                    });
                                }
                            }
                            else {
                                this.set_message({
                                    body: "There is no more product like that to pick",
                                    message_type: "error"
                                });
                            }
                        }
                    },
                    shipFinished: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                        this.lastScanned = null;
                    },
                    shipUnfinished: () => {
                        this.wait_call(
                            this.odoo.call("done", {
                                picking_id: this.state.data.picking.id,
                            })
                        );
                        this.lastScanned = null;
                    },
                    skipPack: () => {
                        this.lastScanned = null;
                        this.state_to('select_document', {skip: parseInt(this.$route.query.skip || 0) + 1});
                    },
                    display_info: {
                        scan_placeholder: () => `${!this.lastScanned ? "Barcode" : ""}${this.lastScanned ? "Quantity, package" : ""} or location`,
                    },
                    fields: [
                        {path: "supplierCode", label: "Vendor code", klass: "loud"},
                        {path: "qty", label: "Quantity"},
                        {path: "qtyDone", label: "Done"},
                        {path: "dest.name", label: "Destination"},
                    ],
                },
                start_line: {
                    display_info: {
                        title: "Pick the product by scanning something",
                        scan_placeholder: "Scan location / pack / product / lot",
                    },
                    // Here we have to use some info sent back from `select`
                    // or from `find_batch` that we pass to scan line
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_line", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                    // Additional actions
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_action_full_bin: () => {
                        this.action_full_bin();
                    },
                    on_action_skip_line: () => {
                        this.wait_call(
                            this.odoo.call("skip_line", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                            })
                        );
                    },
                    on_action_stock_out: () => {
                        this.state_set_data(this.state.data, "stock_issue");
                        this.state_to("stock_issue");
                    },
                    on_action_change_pack_or_lot: () => {
                        this.state_set_data(this.state.data, "change_pack_lot");
                        this.state_to("change_pack_lot");
                    },
                },
                scan_destination: {
                    display_info: {
                        title: "Check qty and scan a destination bin",
                        scan_placeholder: "Scan destination bin",
                    },
                    events: {
                        qty_edit: "on_qty_edit",
                    },
                    enter: () => {
                        // TODO: shalle we hook v-model for qty input straight to the state data?
                        this.scan_destination_qty = this.state_get_data(
                            "start_line"
                        ).quantity;
                    },
                    on_qty_edit: qty => {
                        this.scan_destination_qty = parseInt(qty, 10);
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("scan_destination", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                                barcode: scanned.text,
                                quantity: this.scan_destination_qty,
                            })
                        );
                    },
                    on_action_full_bin: () => {
                        this.action_full_bin();
                    },
                },
                zero_check: {
                    on_action: action => {
                        this.state["on_" + action].call(this);
                    },
                    on_action_confirm_zero: () => {
                        this.wait_call(
                            this.odoo.call("is_zero", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                                zero: true,
                            })
                        );
                    },
                    on_action_confirm_not_zero: () => {
                        this.wait_call(
                            this.odoo.call("is_zero", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                                zero: false,
                            })
                        );
                    },
                },
                unload_all: {
                    display_info: {
                        title: "Unload all bins",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: (scanned, confirmation = false) => {
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("set_destination_all", {
                                picking_batch_id: this.current_batch().id,
                                barcode: scanned.text,
                                confirmation: confirmation,
                            })
                        );
                    },
                    on_action_split: () => {
                        this.wait_call(
                            this.odoo.call("unload_split", {
                                picking_batch_id: this.current_batch().id,
                                barcode: scanned.text, // TODO: should get barcode -> which one? See py specs
                            })
                        );
                    },
                },
                confirm_unload_all: {
                    display_info: {
                        title: "Unload all bins confirm",
                        scan_placeholder: "Scan location",
                    },
                    on_user_confirm: answer => {
                        // TODO: check if this used
                        // -> no flag is set to enable the confirmation dialog,
                        // we only display a message, unlike `confirm_start`
                        if (answer == "yes") {
                            // Reuse data from unload_all
                            const scan_data = this.state_get_data("unload_all");
                            this.state.on_scan(scan_data.location_barcode, true);
                        } else {
                            this.state_to("scan_destination");
                        }
                    },
                    on_scan: (scanned, confirmation = true) => {
                        this.on_state_exit();
                        // FIXME: use state_load or traverse the state
                        // this.current_state_key = "unload_all";
                        // this.state.on_scan(scanned, confirmation);
                        this.states["unload_all"].on_scan(scanned, confirmation);
                    },
                },
                unload_single: {
                    display_info: {
                        title: "Unload single bin",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_pack", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                unload_set_destination: {
                    display_info: {
                        title: "Set destination",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_destination", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                confirm_unload_set_destination: {
                    display_info: {
                        title: "Set destination confirm",
                        scan_placeholder: "Scan location",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("unload_scan_destination", {
                                picking_batch_id: this.current_batch().id,
                                package_id: null, // FIXME: where does it come from? backend data?
                                barcode: scanned.text,
                                confirmation: true,
                            })
                        );
                    },
                },
                change_pack_lot: {
                    display_info: {
                        title: "Change pack or lot",
                        scan_placeholder: "Scan pack or lot",
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("change_pack_lot", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                                barcode: scanned.text,
                            })
                        );
                    },
                },
                stock_issue: {
                    enter: () => {
                        this.reset_notification();
                    },
                    on_confirm_stock_issue: () => {
                        this.wait_call(
                            this.odoo.call("stock_issue", {
                                picking_batch_id: this.current_batch().id,
                                move_line_id: this.state.data.id,
                            })
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("cluster_picking", ClusterPicking);

export default ClusterPicking;
