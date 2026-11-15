"""Data behind the HRDI home page.

แก้เนื้อหาหน้าแรกได้ที่ TODOS / QUICK_ACTIONS / SECTIONS ด้านล่าง
- รายการที่อ้าง model / action ที่ไม่มีในระบบ (แอปยังไม่ติดตั้ง) จะถูกซ่อนอัตโนมัติ
- domain ใช้ "uid" แทนผู้ใช้ปัจจุบัน
"""
import logging

from odoo import api, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

UID = 'uid'

# ---------- งานของฉัน: นับเอกสารที่รอผู้ใช้คนนี้ ----------
TODOS = [
    {'key': 'tier', 'label': 'รอฉันอนุมัติ', 'icon': 'fa-check-square-o', 'tone': 'danger',
     'model': 'tier.review', 'domain': [('status', '=', 'pending'), ('reviewer_ids', 'in', UID)]},
    {'key': 'pr_mine', 'label': 'ใบขอซื้อของฉัน รออนุมัติ', 'icon': 'fa-file-text-o', 'tone': 'warning',
     'model': 'purchase.request', 'domain': [('requested_by', '=', UID), ('state', '=', 'to_approve')]},
    {'key': 'pr_assigned', 'label': 'ใบขอซื้อที่มอบหมายให้ฉัน', 'icon': 'fa-shopping-cart', 'tone': 'info',
     'model': 'purchase.request', 'domain': [('assigned_to', '=', UID), ('state', 'in', ('approved', 'in_progress'))]},
    {'key': 'advance', 'label': 'เงินยืมที่ยังไม่เคลียร์', 'icon': 'fa-money', 'tone': 'warning',
     'model': 'hr.expense.sheet',
     'domain': [('advance', '=', True), ('employee_id.user_id', '=', UID), ('clearing_residual', '>', 0)]},
    {'key': 'repair', 'label': 'ใบแจ้งซ่อมของฉัน (ยังไม่เสร็จ)', 'icon': 'fa-wrench', 'tone': 'info',
     'model': 'maintenance.request', 'domain': [('owner_user_id', '=', UID), ('stage_id.done', '=', False)]},
    {'key': 'activity', 'label': 'กิจกรรม / งานที่ต้องทำ', 'icon': 'fa-clock-o', 'tone': 'secondary',
     'model': 'mail.activity', 'domain': [('user_id', '=', UID)]},
]

# ---------- เริ่มงานด่วน: เปิดฟอร์มสร้างเอกสารใหม่ ----------
QUICK_ACTIONS = [
    {'label': 'ขอซื้อ / ขอจ้าง', 'sub': 'Purchase Request', 'icon': 'fa-file-text-o', 'model': 'purchase.request'},
    {'label': 'ขอยืมเงิน', 'sub': 'Advance', 'icon': 'fa-money',
     'action': 'hr_expense_advance_clearing.action_my_hr_advance_sheet'},
    {'label': 'เบิกค่าใช้จ่าย', 'sub': 'Expense', 'icon': 'fa-file-o', 'model': 'hr.expense'},
    {'label': 'แจ้งซ่อม', 'sub': 'Maintenance', 'icon': 'fa-wrench', 'model': 'maintenance.request'},
    {'label': 'ใบสั่งซื้อ / สัญญา', 'sub': 'Purchase Order', 'icon': 'fa-shopping-cart', 'model': 'purchase.order'},
    {'label': 'บันทึกบิลผู้ขาย', 'sub': 'Vendor Bill', 'icon': 'fa-file-text', 'model': 'account.move',
     'context': {'default_move_type': 'in_invoice'}},
    {'label': 'ขายหน้าร้าน', 'sub': 'Point of Sale', 'icon': 'fa-shopping-basket',
     'action': 'point_of_sale.action_pos_config_kanban'},
]

# ---------- ทางเข้าระบบงาน (จัดกลุ่มตามสายงาน) ----------
SECTIONS = [
    {'key': 'budget', 'label': 'งบประมาณ', 'color': 'purple', 'items': [
        ('แผนงบประมาณ', 'budget_control.budget_plan_action'),
        ('คุมงบ (Budget Control)', 'budget_control.budget_control_action'),
        ('รายงานติดตามงบ', 'budget_control.action_budget_monitor_report_all'),
        ('ยืมเงิน / เคลียร์', 'hr_expense_advance_clearing.action_my_hr_advance_sheet'),
        ('เงินสดย่อย', 'hr_expense_petty_cash.action_petty_cash'),
    ]},
    {'key': 'p2p', 'label': 'จัดซื้อจัดจ้าง', 'color': 'green', 'items': [
        ('ใบขอซื้อ (PR)', 'purchase_request.purchase_request_form_action'),
        ('ใบสั่งซื้อ / สัญญา (PO)', 'purchase.purchase_form_action'),
        ('ตรวจรับงาน', 'purchase_work_acceptance.action_work_acceptance'),
    ]},
    {'key': 'finance', 'label': 'การเงิน / บัญชี', 'color': 'blue', 'items': [
        ('ลูกหนี้ (ใบแจ้งหนี้)', 'account.action_move_out_invoice_type'),
        ('เจ้าหนี้ (บิล)', 'account.action_move_in_invoice_type'),
        ('รับ / จ่ายเงิน', 'account.action_account_payments'),
        ('ภาษีหัก ณ ที่จ่าย', 'l10n_th_account_tax.action_withholding_tax_move_view'),
        ('บัญชีแยกประเภท (GL)', 'account.action_account_moves_all'),
    ]},
    {'key': 'asset', 'label': 'พัสดุ / ครุภัณฑ์', 'color': 'orange', 'items': [
        ('พัสดุ (คลัง)', 'stock.action_picking_tree_all'),
        ('ทะเบียนครุภัณฑ์', 'account_asset_management.account_asset_action'),
        ('แจ้งซ่อมครุภัณฑ์', 'maintenance.hr_equipment_request_action'),
        ('ยานพาหนะ', 'fleet.fleet_vehicle_action'),
    ]},
    {'key': 'o2c', 'label': 'ขาย / บริการ', 'color': 'teal', 'items': [
        ('ใบสั่งขาย', 'sale.action_orders'),
        ('ขายหน้าร้าน (POS)', 'point_of_sale.action_pos_config_kanban'),
    ]},
]

FLOW_ACTION = 'hrdi_flow_map.action_hrdi_flow_map'


class HrdiHome(models.AbstractModel):
    _name = 'hrdi.home'
    _description = 'HRDI Home data provider'

    @api.model
    def get_home_data(self):
        user = self.env.user
        return {
            'user': {'name': user.name, 'company': self.env.company.name},
            'todos': [t for t in (self._todo(spec) for spec in TODOS) if t],
            'quick_actions': [q for q in (self._quick(spec) for spec in QUICK_ACTIONS) if q],
            'sections': [s for s in (self._section(spec) for spec in SECTIONS) if s['items']],
            'flow_action_id': self._action_id(FLOW_ACTION),
        }

    # ---------- helpers ----------
    def _domain(self, domain):
        uid = self.env.uid
        return [(f, op, uid if v == UID else v) for f, op, v in domain]

    def _todo(self, spec):
        Model = self.env.get(spec['model'])
        if Model is None:
            return None
        domain = self._domain(spec['domain'])
        try:
            count = Model.search_count(domain)
        except AccessError:
            return None
        except Exception:  # noqa: BLE001 - one broken counter must not break the page
            _logger.exception('hrdi_home: todo %s failed', spec['key'])
            return None
        return {**{k: spec[k] for k in ('key', 'label', 'icon', 'tone', 'model')}, 'domain': domain, 'count': count}

    def _quick(self, spec):
        res = {k: spec.get(k) for k in ('label', 'sub', 'icon', 'model', 'context')}
        if spec.get('action'):
            res['action_id'] = self._action_id(spec['action'])
            return res if res['action_id'] else None
        Model = self.env.get(spec['model'])
        if Model is None or not Model.has_access('create'):
            return None
        return res

    def _section(self, spec):
        items = []
        for label, xmlid in spec['items']:
            action_id = self._action_id(xmlid)
            if action_id:
                items.append({'label': label, 'action_id': action_id})
        return {'key': spec['key'], 'label': spec['label'], 'color': spec['color'], 'items': items}

    def _action_id(self, xmlid):
        action = self.env.ref(xmlid, raise_if_not_found=False)
        return action.id if action else False
