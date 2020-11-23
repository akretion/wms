/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("item-detail-card", {
    mixins: [ItemDetailMixin],
    props: ["card_color", "outlined"],
    template: `
    <div :class="wrapper_klass">
        <v-card
            :color="card_color"
            tile
            :class="{'main': opts.main, 'no-outline': opts.no_outline}"
            v-if="!_.isEmpty(record)"
            v-on="opts.on_click_action ? {click: opts.on_click_action} : {}"
            :outlined="outlined"
            >
            <v-card-title v-if="!opts.no_title">
                <slot name="title">
                    <v-icon v-if="opts.title_icon" v-text="opts.title_icon" class="mr-2" />
                    <span v-text="_.result(record, opts.key_title)" />
                    <v-btn icon class="detail-action" link
                            v-if="opts.on_title_action || opts.title_action_field"
                            v-on="opts.on_title_action ? {click: opts.on_title_action} : {}">
                        <btn-info-icon />
                    </v-btn>
                </slot>
            </v-card-title>
            <v-card-subtitle v-if="$slots.subtitle">
                <slot name="subtitle"></slot>
            </v-card-subtitle>
            <slot name="details">
                <!-- TODO: this loop is the same in list-item => make it a component -->
                <v-card-text class="details" v-if="opts.fields.length">
                    <div v-for="(field, index) in opts.fields" :class="'field-detail ' + field.path.replace('.', '-') + ' ' + (field.klass || '')">
                        <div v-if="raw_value(record, field) !== undefined || field.display_no_value">
                            <span v-if="field.label" class="label">{{ field.label }}:</span>
                            <component
                                v-if="field.render_component"
                                :is="field.render_component"
                                :options="field.render_options ? field.render_options(record) : {}"
                                :record="record"
                                :key="make_component_key([field.render_component, 'list', index, record.id])"
                                />
                            <span v-else>
                                {{ render_field_value(record, field) }}
                            </span>
                            <v-btn icon class="detail-action"
                                    v-if="has_detail_action(record, field)"
                                    @click="on_detail_action(record, field, opts)">
                                <btn-info-icon />
                            </v-btn>
                        </div>
                    </div>
                </v-card-text>
            </slot>
            <slot name="after_details"></slot>
        </v-card>
        <p v-if="_.isEmpty(record)">
            No detail record to display.
        </p>
    </div>
  `,
    renderTriggered() {
        console.log(this.opts.on_click_action);
    },
});
