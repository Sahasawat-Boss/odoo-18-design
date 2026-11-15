/** @odoo-module **/
import { Component, onMounted, onPatched, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const KIND_LABEL = { flow: "ขั้นตอนในสาย", budget: "เชื่อมงบประมาณ", cross: "ข้ามสาย" };

export class HrdiFlowMap extends Component {
    static template = "hrdi_flow_map.FlowMap";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.canvas = useRef("canvas");
        this.state = useState({ data: null, selected: null, edges: [], loading: true });
        this.kindLabel = KIND_LABEL;
        this.numberFmt = new Intl.NumberFormat("th-TH", { maximumFractionDigits: 0 });

        onWillStart(() => this.load());
        onMounted(() => {
            this.drawEdges();
            this.resizeObserver = new ResizeObserver(() => this.drawEdges());
            this.resizeObserver.observe(this.canvas.el);
        });
        onPatched(() => this.drawEdges());
        onWillUnmount(() => this.resizeObserver?.disconnect());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("hrdi.flow.map", "get_flow_data", []);
        this.state.loading = false;
    }

    // ---------- data helpers ----------
    get lanes() {
        return this.state.data.lanes.map((lane) => ({
            ...lane,
            nodes: this.state.data.nodes.filter((n) => n.lane === lane.key),
        }));
    }
    get glNode() {
        return this.state.data.nodes.find((n) => n.lane === "gl");
    }
    get selectedNode() {
        return this.state.data?.nodes.find((n) => n.key === this.state.selected);
    }
    get selectedEdges() {
        const key = this.state.selected;
        const byKey = Object.fromEntries(this.state.data.nodes.map((n) => [n.key, n]));
        return this.state.data.edges
            .filter((e) => e.from === key || e.to === key)
            .map((e) => ({
                ...e,
                dir: e.from === key ? "→" : "←",
                other: byKey[e.from === key ? e.to : e.from]?.label,
            }));
    }
    formatAmount(value) {
        const cur = this.state.data.currency;
        const num = this.numberFmt.format(value);
        return cur.position === "before" ? `${cur.symbol} ${num}` : `${num} ${cur.symbol}`;
    }
    isDimmed(nodeKey) {
        const sel = this.state.selected;
        if (!sel || sel === nodeKey) {
            return false;
        }
        return !this.state.data.edges.some(
            (e) => (e.from === sel && e.to === nodeKey) || (e.to === sel && e.from === nodeKey)
        );
    }

    // ---------- actions ----------
    onSelect(node) {
        this.state.selected = this.state.selected === node.key ? null : node.key;
    }
    async openNode(node) {
        if (node.action_id) {
            return this.action.doAction(node.action_id);
        }
        if (node.fallback) {
            return this.openList(node.label, node.fallback.model, node.fallback.domain);
        }
    }
    openMetric(metric, ev) {
        ev.stopPropagation();
        if (metric.count !== null && !metric.denied) {
            this.openList(metric.label, metric.model, metric.domain);
        }
    }
    openList(name, model, domain) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }
    async refresh() {
        await this.load();
    }

    // ---------- SVG connectors ----------
    drawEdges() {
        const canvasEl = this.canvas.el;
        if (!canvasEl || !this.state.data) {
            return;
        }
        const base = canvasEl.getBoundingClientRect();
        const rects = {};
        for (const el of canvasEl.querySelectorAll("[data-node]")) {
            const r = el.getBoundingClientRect();
            rects[el.dataset.node] = {
                left: r.left - base.left,
                right: r.right - base.left,
                top: r.top - base.top,
                bottom: r.bottom - base.top,
                cx: r.left - base.left + r.width / 2,
                cy: r.top - base.top + r.height / 2,
                h: r.height,
            };
        }
        const laneIndex = Object.fromEntries(this.state.data.lanes.map((l, i) => [l.key, i]));
        const nodeByKey = Object.fromEntries(this.state.data.nodes.map((n) => [n.key, n]));
        const posInLane = {};
        for (const lane of this.state.data.lanes) {
            this.state.data.nodes.filter((n) => n.lane === lane.key).forEach((n, i) => (posInLane[n.key] = i));
        }

        // a lane whose right side is free of cross-lane edges loops on the right, otherwise on the left
        const busyRight = new Set();
        for (const edge of this.state.data.edges) {
            const la = laneIndex[nodeByKey[edge.from].lane];
            const lb = laneIndex[nodeByKey[edge.to].lane];
            if (la !== lb) {
                busyRight.add(Math.min(la, lb));
            }
        }

        // 1st pass: decide which side of each card an edge attaches to
        const plans = [];
        for (const edge of this.state.data.edges) {
            const a = rects[edge.from];
            const b = rects[edge.to];
            if (!a || !b) {
                continue;
            }
            const la = laneIndex[nodeByKey[edge.from].lane];
            const lb = laneIndex[nodeByKey[edge.to].lane];
            let plan;
            if (la === lb) {
                const adjacent = Math.abs(posInLane[edge.from] - posInLane[edge.to]) === 1;
                if (adjacent) {
                    plan = b.top > a.bottom
                        ? { edge, type: "v", fromSide: "bottom", toSide: "top" }
                        : { edge, type: "v", fromSide: "top", toSide: "bottom" };
                } else {
                    const side = busyRight.has(la) ? "left" : "right";
                    plan = { edge, type: "loop", fromSide: side, toSide: side };
                }
            } else if (la < lb) {
                plan = { edge, type: "h", fromSide: "right", toSide: "left" };
            } else {
                plan = { edge, type: "h", fromSide: "left", toSide: "right" };
            }
            plans.push(plan);
        }
        // spread several connectors sharing the same card side
        const slots = {};
        const slotKey = (node, side) => `${node}:${side}`;
        for (const p of plans) {
            (slots[slotKey(p.edge.from, p.fromSide)] ||= []).push(p);
            (slots[slotKey(p.edge.to, p.toSide)] ||= []).push(p);
        }
        const anchor = (node, side, plan) => {
            const r = rects[node];
            const group = slots[slotKey(node, side)];
            const i = group.indexOf(plan);
            const frac = (i + 1) / (group.length + 1);
            switch (side) {
                case "top":
                    return { x: r.cx, y: r.top };
                case "bottom":
                    return { x: r.cx, y: r.bottom };
                case "left":
                    return { x: r.left, y: r.top + r.h * frac };
                default:
                    return { x: r.right, y: r.top + r.h * frac };
            }
        };

        const edges = plans.map((p) => {
            const s = anchor(p.edge.from, p.fromSide, p);
            const t = anchor(p.edge.to, p.toSide, p);
            let c1;
            let c2;
            if (p.type === "v") {
                c1 = { x: s.x, y: (s.y + t.y) / 2 };
                c2 = { x: t.x, y: (s.y + t.y) / 2 };
            } else if (p.type === "loop") {
                const x = p.fromSide === "left" ? Math.min(s.x, t.x) - 34 : Math.max(s.x, t.x) + 34;
                c1 = { x, y: s.y };
                c2 = { x, y: t.y };
            } else {
                const dx = (t.x - s.x) / 2;
                c1 = { x: s.x + dx, y: s.y };
                c2 = { x: t.x - dx, y: t.y };
            }
            const mid = {
                x: (s.x + 3 * c1.x + 3 * c2.x + t.x) / 8,
                y: (s.y + 3 * c1.y + 3 * c2.y + t.y) / 8,
            };
            const sel = this.state.selected;
            return {
                id: `${p.edge.from}-${p.edge.to}`,
                kind: p.edge.kind,
                label: p.edge.label,
                d: `M ${s.x} ${s.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${t.x} ${t.y}`,
                lx: mid.x,
                ly: mid.y,
                active: !sel || p.edge.from === sel || p.edge.to === sel,
            };
        });
        // only touch state when geometry really changed (avoids a render loop with onPatched)
        if (JSON.stringify(edges) !== JSON.stringify(this.state.edges)) {
            this.state.edges = edges;
        }
    }
}

registry.category("actions").add("hrdi_flow_map", HrdiFlowMap);
