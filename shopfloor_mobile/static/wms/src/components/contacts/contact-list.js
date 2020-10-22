/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("contact-list", {
    props: ["contacts"],
    template: `
        <contact-detail :contact="contact" v-for="contact in contacts" v-key="contact.code"/>
    `,
}),
