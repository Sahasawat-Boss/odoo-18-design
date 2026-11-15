"""Data behind the flow map.

แก้ "แผนผัง" ได้ที่ LANES / NODES / EDGES ด้านล่างอย่างเดียว หน้าจอ (OWL) วาดตามข้อมูลนี้
- tag:     std = Odoo มาตรฐาน, oca = OCA/Ecosoft, custom = ต้องพัฒนาเอง
- metrics: จำนวน (และยอดเงิน) ที่นับจาก DB จริง ตามสิทธิ์ของผู้ใช้ที่เปิดดู
- open:    action xmlid ที่จะเปิดเมื่อกด ถ้าหาไม่เจอจะเปิด list ของ model แรกใน metrics แทน
"""
import logging

from odoo import api, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

LANES = [
    {'key': 'o2c', 'label': 'Order-to-Cash', 'sub': 'ขาย → รับเงิน'},
    {'key': 'budget', 'label': 'งบประมาณ', 'sub': 'หัวใจของงานรัฐ: คุมทุกการใช้เงิน'},
    {'key': 'p2p', 'label': 'Procure-to-Pay', 'sub': 'ซื้อ → จ่าย'},
    {'key': 'asset', 'label': 'พัสดุ / ครุภัณฑ์', 'sub': 'รับเข้า → ทะเบียน → ดูแล'},
]

NODES = [
    # ---------------- Order-to-Cash ----------------
    {
        'key': 'sale', 'lane': 'o2c', 'tag': 'std',
        'label': 'ขาย / ขายหน้าร้าน', 'apps': 'Sales + POS',
        'modules': ['sale_management', 'point_of_sale'],
        'desc': 'ใบเสนอราคา → ใบสั่งขาย และการขายหน้าร้านผ่าน POS',
        'tables': ['sale_order', 'sale_order_line', 'pos_order', 'pos_order_line'],
        'metrics': [
            {'label': 'ใบสั่งขาย', 'model': 'sale.order', 'domain': [('state', '=', 'sale')], 'sum': 'amount_total'},
            {'label': 'บิล POS', 'model': 'pos.order', 'domain': [('state', 'in', ('paid', 'done', 'invoiced'))], 'sum': 'amount_total'},
        ],
        'open': 'sale.action_orders',
        'gl': True,
    },
    {
        'key': 'venue', 'lane': 'o2c', 'tag': 'custom',
        'label': 'โรงแรม / สถานที่', 'apps': 'hrdi_venue (ยังไม่พัฒนา)',
        'modules': ['hrdi_venue'],
        'desc': 'จองห้องพัก / ห้องประชุม / สถานที่ แล้วส่งต่อเป็นใบแจ้งหนี้ลูกหนี้',
        'tables': [],
        'metrics': [],
    },
    {
        'key': 'ar', 'lane': 'o2c', 'tag': 'std',
        'label': 'บัญชีลูกหนี้', 'apps': 'Customer Invoices',
        'modules': ['account'],
        'desc': 'ใบแจ้งหนี้ / ใบกำกับภาษีขาย (ภาษีขายลง l10n_th_account_tax)',
        'tables': ['account_move (move_type=out_invoice)', 'account_move_line'],
        'metrics': [
            {'label': 'ใบแจ้งหนี้ posted', 'model': 'account.move',
             'domain': [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], 'sum': 'amount_residual_signed',
             'sum_label': 'ค้างรับ'},
        ],
        'open': 'account.action_move_out_invoice_type',
        'gl': True,
    },
    {
        'key': 'receipt', 'lane': 'o2c', 'tag': 'std',
        'label': 'รับเงิน / เช็ครับ', 'apps': 'Payments',
        'modules': ['account'],
        'desc': 'รับชำระและกระทบยอดกับใบแจ้งหนี้ (การติดตามสถานะเช็ค: ต้องตรวจ gap เพิ่ม)',
        'tables': ['account_payment', 'account_move', 'account_partial_reconcile'],
        'metrics': [
            {'label': 'รับชำระ', 'model': 'account.payment', 'domain': [('payment_type', '=', 'inbound')], 'sum': 'amount'},
        ],
        'open': 'account.action_account_payments',
        'gl': True,
    },
    # ---------------- Budget ----------------
    {
        'key': 'bplan', 'lane': 'budget', 'tag': 'oca',
        'label': 'แผนงบประมาณ', 'apps': 'budget_control (Ecosoft)',
        'modules': ['budget_control'],
        'desc': 'ตั้งงบประจำปี (Budget Plan) แยกตาม Analytic Account / หน่วยงาน',
        'tables': ['budget_plan', 'budget_plan_line', 'budget_period'],
        'metrics': [{'label': 'แผน', 'model': 'budget.plan', 'domain': []}],
        'open': 'budget_control.budget_plan_action',
    },
    {
        'key': 'bcontrol', 'lane': 'budget', 'tag': 'oca',
        'label': 'คุมงบ (Budget Control)', 'apps': 'budget_control',
        'modules': ['budget_control'],
        'desc': 'ยอดงบที่อนุมัติต่อ Analytic: งบ − กันงบ − ใช้จริง = คงเหลือ ใช้ตรวจก่อนอนุมัติทุกเอกสาร',
        'tables': ['budget_control', 'budget_control_line', 'budget_monitor_report (view)'],
        'metrics': [{'label': 'Budget Control Sheet', 'model': 'budget.control', 'domain': []}],
        'open': 'budget_control.budget_control_action',
    },
    {
        'key': 'commit', 'lane': 'budget', 'tag': 'oca',
        'label': 'กันงบ (Commitment)', 'apps': 'budget_control_purchase_request / _purchase / _advance_clearing',
        'modules': ['budget_control'],
        'desc': 'ทุกเอกสารที่อนุมัติจะสร้าง budget move: PR → PO → บิล (กันงบย้ายต่อเป็นทอดๆ จนเป็นใช้จริง)',
        'tables': ['purchase_request_budget_move', 'purchase_budget_move', 'advance_budget_move',
                   'expense_budget_move', 'account_budget_move'],
        'metrics': [
            {'label': 'กันงบ PR', 'model': 'purchase.request.budget.move', 'domain': [], 'net': True},
            {'label': 'กันงบ PO', 'model': 'purchase.budget.move', 'domain': [], 'net': True},
            {'label': 'กันงบ ยืมเงิน', 'model': 'advance.budget.move', 'domain': [], 'net': True},
            {'label': 'ใช้จริง (Actual)', 'model': 'account.budget.move', 'domain': [], 'net': True},
        ],
        'open': 'budget_control.budget_control_action',
    },
    {
        'key': 'advance', 'lane': 'budget', 'tag': 'oca',
        'label': 'ยืมเงิน → จ่าย → เคลียร์', 'apps': 'hr_expense_advance_clearing',
        'modules': ['hr_expense_advance_clearing'],
        'desc': 'ใบยืมเงินกันงบ → จ่ายเงินยืม → ส่งใบเคลียร์ (คืนเงิน / เบิกเพิ่ม) แล้วงบย้ายเป็นใช้จริง',
        'tables': ['hr_expense_sheet (advance=true)', 'hr_expense', 'advance_budget_move'],
        'metrics': [
            {'label': 'ใบยืม', 'model': 'hr.expense.sheet', 'domain': [('advance', '=', True)], 'sum': 'total_amount'},
            {'label': 'ใบเคลียร์', 'model': 'hr.expense.sheet', 'domain': [('advance_sheet_id', '!=', False)]},
        ],
        'open': 'hr_expense_advance_clearing.action_my_hr_advance_sheet',
        'gl': True,
    },
    {
        'key': 'petty', 'lane': 'budget', 'tag': 'oca',
        'label': 'เงินสดย่อย', 'apps': 'hr_expense_petty_cash',
        'modules': ['hr_expense_petty_cash'],
        'desc': 'วงเงินสดย่อยรายผู้ถือ เบิกชดเชยแล้วตัดงบ',
        'tables': ['petty_cash', 'petty_cash_transaction'],
        'metrics': [{'label': 'วงเงินสดย่อย', 'model': 'petty.cash', 'domain': []}],
        'open': 'hr_expense_petty_cash.action_petty_cash',
        'gl': True,
    },
    # ---------------- Procure-to-Pay ----------------
    {
        'key': 'pr', 'lane': 'p2p', 'tag': 'oca',
        'label': 'ใบขอซื้อ (PR)', 'apps': 'purchase_request + l10n_th_gov_purchase_request',
        'modules': ['purchase_request'],
        'desc': 'หน่วยงานขอซื้อ/จ้าง ระบบตรวจและกันงบตั้งแต่ขั้นนี้',
        'tables': ['purchase_request', 'purchase_request_line'],
        'metrics': [{'label': 'PR', 'model': 'purchase.request', 'domain': []}],
        'open': 'purchase_request.purchase_request_form_action',
    },
    {
        'key': 'po', 'lane': 'p2p', 'tag': 'std',
        'label': 'จัดซื้อจัดจ้าง / สัญญา (PO)', 'apps': 'Purchase',
        'modules': ['purchase'],
        'desc': 'ใบสั่งซื้อ / สัญญา (กันงบย้ายจาก PR มาที่ PO)',
        'tables': ['purchase_order', 'purchase_order_line'],
        'metrics': [{'label': 'PO ยืนยันแล้ว', 'model': 'purchase.order',
                     'domain': [('state', 'in', ('purchase', 'done'))], 'sum': 'amount_total'}],
        'open': 'purchase.purchase_form_action',
    },
    {
        'key': 'wa', 'lane': 'p2p', 'tag': 'oca',
        'label': 'ตรวจรับงาน', 'apps': 'purchase_work_acceptance + คณะกรรมการ (custom)',
        'modules': ['purchase_work_acceptance'],
        'desc': 'คณะกรรมการตรวจรับพัสดุ/งานจ้าง ก่อนรับเข้าคลังและตั้งเจ้าหนี้ (ส่วนคณะกรรมการต้อง custom)',
        'tables': ['work_acceptance', 'work_acceptance_line'],
        'metrics': [{'label': 'ใบตรวจรับ', 'model': 'work.acceptance', 'domain': []}],
        'open': 'purchase_work_acceptance.action_work_acceptance',
        'custom_ext': 'คณะกรรมการตรวจรับ',
    },
    {
        'key': 'ap', 'lane': 'p2p', 'tag': 'std',
        'label': 'เจ้าหนี้', 'apps': 'Vendor Bills',
        'modules': ['account'],
        'desc': 'บิลผู้ขาย / ภาษีซื้อ — กันงบ PO กลายเป็น "ใช้จริง"',
        'tables': ['account_move (move_type=in_invoice)', 'account_move_line', 'account_budget_move'],
        'metrics': [{'label': 'บิล posted', 'model': 'account.move',
                     'domain': [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
                     'sum': 'amount_residual_signed', 'sum_label': 'ค้างจ่าย'}],
        'open': 'account.action_move_in_invoice_type',
        'gl': True,
    },
    {
        'key': 'pay', 'lane': 'p2p', 'tag': 'std',
        'label': 'จ่ายเงิน + หัก ณ ที่จ่าย', 'apps': 'Payments + l10n_th_account_tax',
        'modules': ['account'],
        'desc': 'จ่ายชำระเจ้าหนี้ หักภาษี ณ ที่จ่าย และออกหนังสือรับรอง 50 ทวิ',
        'tables': ['account_payment', 'account_withholding_move'],
        'metrics': [
            {'label': 'จ่ายชำระ', 'model': 'account.payment', 'domain': [('payment_type', '=', 'outbound')], 'sum': 'amount'},
            {'label': 'รายการหัก ณ ที่จ่าย', 'model': 'account.withholding.move', 'domain': []},
        ],
        'open': 'account.action_account_payments_payable',
        'gl': True,
    },
    # ---------------- Inventory / Assets ----------------
    {
        'key': 'stock', 'lane': 'asset', 'tag': 'std',
        'label': 'พัสดุ', 'apps': 'Inventory',
        'modules': ['stock'],
        'desc': 'รับเข้า / เบิกจ่ายพัสดุ (ตัดงบเมื่อเบิกใช้ ด้วย budget_control_stock ถ้าต้องการ)',
        'tables': ['stock_picking', 'stock_move', 'stock_quant'],
        'metrics': [{'label': 'ใบรับ/จ่าย done', 'model': 'stock.picking', 'domain': [('state', '=', 'done')]}],
        'open': 'stock.action_picking_tree_all',
        'gl': True,
    },
    {
        'key': 'fa', 'lane': 'asset', 'tag': 'oca',
        'label': 'ครุภัณฑ์', 'apps': 'account_asset_management + l10n_th',
        'modules': ['account_asset_management'],
        'desc': 'ทะเบียนครุภัณฑ์ เลขครุภัณฑ์ โอนย้าย และค่าเสื่อมราคาลง GL',
        'tables': ['account_asset', 'account_asset_line', 'account_asset_profile'],
        'metrics': [{'label': 'ครุภัณฑ์', 'model': 'account.asset', 'domain': [], 'sum': 'purchase_value'}],
        'open': 'account_asset_management.account_asset_action',
        'gl': True,
    },
    {
        'key': 'mr', 'lane': 'asset', 'tag': 'std',
        'label': 'แจ้งซ่อมครุภัณฑ์', 'apps': 'Maintenance',
        'modules': ['maintenance'],
        'desc': 'แจ้งซ่อม / บำรุงรักษาตามแผน (ผูกกับทะเบียนครุภัณฑ์อาจต้อง custom)',
        'tables': ['maintenance_request', 'maintenance_equipment'],
        'metrics': [{'label': 'ใบแจ้งซ่อม', 'model': 'maintenance.request', 'domain': []}],
        'open': 'maintenance.hr_equipment_request_action',
    },
    {
        'key': 'fleet', 'lane': 'asset', 'tag': 'std',
        'label': 'ยานพาหนะ', 'apps': 'Fleet',
        'modules': ['fleet'],
        'desc': 'ทะเบียนรถ สัญญา ค่าใช้จ่ายรถ',
        'tables': ['fleet_vehicle', 'fleet_vehicle_log_services'],
        'metrics': [{'label': 'รถ', 'model': 'fleet.vehicle', 'domain': []}],
        'open': 'fleet.fleet_vehicle_action',
    },
    # ---------------- GL ----------------
    {
        'key': 'gl', 'lane': 'gl', 'tag': 'std',
        'label': 'บัญชีแยกประเภท (GL)', 'apps': 'Accounting + Analytic + ภาษีซื้อ/ขาย/หัก ณ ที่จ่าย (l10n-thailand)',
        'modules': ['account'],
        'desc': 'ทุกเอกสารที่ post จะลง account_move_line พร้อม Analytic (= มิติงบประมาณ) และภาษี',
        'tables': ['account_move', 'account_move_line', 'account_analytic_line', 'account_tax'],
        'metrics': [
            {'label': 'รายการบัญชี (posted)', 'model': 'account.move.line', 'domain': [('parent_state', '=', 'posted')]},
            {'label': 'Analytic lines', 'model': 'account.analytic.line', 'domain': []},
        ],
        'open': 'account.action_account_moves_all',
    },
]

# kind: flow = ภายในสาย, budget = เชื่อมกับงบประมาณ, cross = ข้ามสาย
EDGES = [
    ('sale', 'ar', 'ออกใบแจ้งหนี้', 'flow'),
    ('venue', 'ar', 'วางบิลค่าห้อง', 'flow'),
    ('ar', 'receipt', 'รับชำระ', 'flow'),
    ('bplan', 'bcontrol', 'อนุมัติ/จัดสรรงบ', 'flow'),
    ('bcontrol', 'commit', 'ตรวจงบคงเหลือ', 'flow'),
    ('pr', 'po', 'สร้าง PO', 'flow'),
    ('po', 'wa', 'ส่งมอบ', 'flow'),
    ('wa', 'ap', 'วางบิล', 'flow'),
    ('ap', 'pay', 'จ่ายเงิน', 'flow'),
    ('stock', 'fa', 'ขึ้นทะเบียน', 'flow'),
    ('fa', 'mr', 'แจ้งซ่อม', 'flow'),
    ('fa', 'fleet', 'รถ = ครุภัณฑ์', 'flow'),
    ('pr', 'commit', 'กันงบ PR', 'budget'),
    ('po', 'commit', 'กันงบ PO', 'budget'),
    ('ap', 'commit', 'ใช้จริง', 'budget'),
    ('advance', 'commit', 'กันงบยืมเงิน', 'budget'),
    ('petty', 'commit', 'ตัดงบ', 'budget'),
    ('wa', 'stock', 'รับเข้าคลัง / ครุภัณฑ์', 'cross'),
]


class HrdiFlowMap(models.AbstractModel):
    _name = 'hrdi.flow.map'
    _description = 'HRDI Flow Map data provider'

    @api.model
    def get_flow_data(self):
        installed = set(self.env['ir.module.module'].sudo().search(
            [('state', '=', 'installed')]).mapped('name'))
        nodes = []
        for spec in NODES:
            node = {k: v for k, v in spec.items() if k not in ('metrics', 'open', 'modules')}
            node['modules'] = spec['modules']
            node['installed'] = all(m in installed for m in spec['modules'])
            node['metrics'] = [self._metric(m) for m in spec['metrics']] if node['installed'] else []
            node['action_id'] = self._action_id(spec.get('open'))
            first = spec['metrics'][0] if spec['metrics'] else None
            node['fallback'] = {'model': first['model'], 'domain': first['domain']} if first else False
            nodes.append(node)
        edges = [{'from': f, 'to': t, 'label': lbl, 'kind': kind} for f, t, lbl, kind in EDGES]
        currency = self.env.company.currency_id
        return {
            'lanes': LANES,
            'nodes': nodes,
            'edges': edges,
            'currency': {'symbol': currency.symbol, 'position': currency.position},
        }

    def _metric(self, spec):
        res = {'label': spec['label'], 'count': None, 'amount': None, 'sum_label': spec.get('sum_label'),
               'model': spec['model'], 'domain': spec['domain']}
        Model = self.env.get(spec['model'])
        if Model is None:
            return res
        try:
            domain = spec['domain']
            res['count'] = Model.search_count(domain)
            if spec.get('net'):
                # budget move: ยอดคงค้างของกันงบ = debit - credit
                [(debit, credit)] = Model._read_group(domain, [], ['debit:sum', 'credit:sum'])
                res['amount'] = (debit or 0.0) - (credit or 0.0)
            elif spec.get('sum') and spec['sum'] in Model._fields:
                [(total,)] = Model._read_group(domain, [], [f"{spec['sum']}:sum"])
                # *_signed ฝั่งเจ้าหนี้เป็นค่าลบ -> แสดงเป็นยอดบวก
                res['amount'] = abs(total or 0.0)
        except AccessError:
            res['denied'] = True
        except Exception:  # noqa: BLE001 - a broken metric must not break the whole map
            _logger.exception('hrdi_flow_map: metric failed for %s', spec['model'])
        return res

    def _action_id(self, xmlid):
        if not xmlid:
            return False
        action = self.env.ref(xmlid, raise_if_not_found=False)
        return action.id if action else False
