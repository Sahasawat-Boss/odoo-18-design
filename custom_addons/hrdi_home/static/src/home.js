/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class HrdiHome extends Component {
    static template = "hrdi_home.Home";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null });
        // th-TH uses the Buddhist calendar: "วันอาทิตย์ที่ 15 พฤศจิกายน พ.ศ. 2569"
        this.today = new Intl.DateTimeFormat("th-TH", { dateStyle: "full" }).format(new Date());
        onWillStart(() => this.load());
    }

    async load() {
        this.state.data = await this.orm.call("hrdi.home", "get_home_data", []);
    }

    get greeting() {
        const h = new Date().getHours();
        return h < 12 ? "สวัสดีตอนเช้า" : h < 17 ? "สวัสดีตอนบ่าย" : "สวัสดีตอนเย็น";
    }

    openTodo(todo) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: todo.label,
            res_model: todo.model,
            domain: todo.domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }

    openQuick(quick) {
        if (quick.action_id) {
            return this.action.doAction(quick.action_id);
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: quick.label,
            res_model: quick.model,
            views: [[false, "form"]],
            target: "current",
            context: quick.context || {},
        });
    }

    openAction(actionId) {
        return this.action.doAction(actionId);
    }
}

registry.category("actions").add("hrdi_home", HrdiHome);
