"""Small HRDI demo dataset, created through the real workflows (not raw inserts)
so budget moves (commitments) are generated exactly like in production.

    หน่วยงาน (analytic) 2 แห่ง
      -> แผนงบประมาณ -> Budget Control Sheet ต่อหน่วยงาน (จัดสรรงบ + Control)
      -> ใบขอซื้อ 1 ใบ อนุมัติแล้ว (กันงบจริง) + 1 ใบ รออนุมัติ

Re-running is safe: if the plan already exists nothing is created.
Run manually:  odoo-bin shell ... >>> from odoo.addons.hrdi_demo_data.loader import load; load(env)
"""
import logging

from odoo import Command, fields

_logger = logging.getLogger(__name__)

MODULE = 'hrdi_demo_data'
PERIOD_XMLID = 'budget_control.budget_period_demo'

DEPARTMENTS = [
    # (xmlid, code, name, budget)
    ('aa_research', 'HRDI-R', 'ฝ่ายวิจัย', 600_000.0),
    ('aa_admin', 'HRDI-A', 'ฝ่ายบริหารงานทั่วไป', 400_000.0),
]

PRODUCTS = [
    # (xmlid, name, expense account xmlid, cost)
    ('prod_paper', 'กระดาษ A4 80 แกรม (รีม)', 'account.1_expense', 120.0),
    ('prod_notebook', 'โน้ตบุ๊กสำหรับงานวิจัย', 'account.1_expense_invest', 32_000.0),
]


def _ref(env, name):
    return env.ref(f'{MODULE}.{name}', raise_if_not_found=False)


def _bind(env, name, record):
    """Give the record an xmlid hrdi_demo_data.<name> (so it is findable and removed on uninstall)."""
    env['ir.model.data'].create({
        'module': MODULE, 'name': name, 'model': record._name, 'res_id': record.id, 'noupdate': True,
    })
    return record


def load(env):
    if _ref(env, 'budget_plan'):
        _logger.info('hrdi_demo_data: already loaded, skipping')
        return
    period = env.ref(PERIOD_XMLID, raise_if_not_found=False)
    if not period:
        _logger.warning('hrdi_demo_data: %s not found (budget_control demo data off?) - skipping', PERIOD_XMLID)
        return
    company = env.company
    admin = env.ref('base.user_admin')

    # ---------- 1) หน่วยงาน = analytic accounts ----------
    plan = _bind(env, 'aa_plan', env['account.analytic.plan'].create({'name': 'หน่วยงาน HRDI'}))
    analytics = {}
    for xmlid, code, name, _budget in DEPARTMENTS:
        analytics[xmlid] = _bind(env, xmlid, env['account.analytic.account'].create({
            'name': name, 'code': code, 'plan_id': plan.id, 'company_id': company.id,
        }))

    # ---------- 2) สินค้า/บริการ ที่ผูกบัญชีค่าใช้จ่ายตาม KPI ของ template ----------
    products = {}
    for xmlid, name, account_xmlid, cost in PRODUCTS:
        products[xmlid] = _bind(env, xmlid, env['product.product'].create({
            'name': name,
            'type': 'consu',
            'standard_price': cost,
            'purchase_ok': True,
            'property_account_expense_id': env.ref(account_xmlid).id,
        }))

    # ---------- 3) แผนงบ -> Budget Control Sheet (จัดสรร + Control) ----------
    budget_plan = _bind(env, 'budget_plan', env['budget.plan'].create({
        'name': f'แผนงบประมาณ HRDI {period.name} (ตัวอย่าง)',
        'budget_period_id': period.id,
        'line_ids': [
            Command.create({'analytic_account_id': analytics[xmlid].id, 'amount': budget})
            for xmlid, _code, _name, budget in DEPARTMENTS
        ],
    }))
    budget_plan.action_confirm()
    budget_plan.action_create_update_budget_control()
    budget_plan.action_done()
    budget_plan.invalidate_recordset()

    template_lines = period.template_id.line_ids
    for control in budget_plan.budget_control_ids:
        control.template_line_ids = [Command.set(template_lines.ids)]
        control.prepare_budget_control_matrix()
        # แบ่งงบเท่าๆ กันทุก KPI x ทุกไตรมาส
        budget = next(b for x, _c, _n, b in DEPARTMENTS if analytics[x] == control.analytic_account_id)
        # ผลรวมต้องเท่ายอดที่ released พอดี -> เศษจากการปัดไปไว้ช่องสุดท้าย
        lines = control.line_ids
        per_line = round(budget / len(lines), 2)
        lines[:-1].write({'amount': per_line})
        lines[-1].amount = round(budget - per_line * (len(lines) - 1), 2)
        control.action_submit()
        control.action_done()

    # ---------- 4) ใบขอซื้อ ----------
    PR = env['purchase.request'].with_context(force_date_commit=fields.Date.context_today(admin))
    pr_approved = _bind(env, 'pr_approved', PR.create({
        'description': 'จัดซื้อโน้ตบุ๊กสำหรับโครงการวิจัยพืชเมืองหนาว',
        'requested_by': admin.id,
        'line_ids': [Command.create({
            'product_id': products['prod_notebook'].id,
            'product_qty': 2,
            'estimated_cost': 64_000.0,
            'analytic_distribution': {str(analytics['aa_research'].id): 100},
        })],
    }))
    pr_approved.button_to_approve()
    pr_approved.button_approved()  # -> กันงบ (purchase.request.budget.move)

    pr_waiting = _bind(env, 'pr_waiting', PR.create({
        'description': 'จัดซื้อวัสดุสำนักงานประจำไตรมาส',
        'requested_by': admin.id,
        'line_ids': [Command.create({
            'product_id': products['prod_paper'].id,
            'product_qty': 50,
            'estimated_cost': 6_000.0,
            'analytic_distribution': {str(analytics['aa_admin'].id): 100},
        })],
    }))
    pr_waiting.button_to_approve()  # รออนุมัติ (ยังไม่กันงบ)

    _logger.info('hrdi_demo_data: loaded plan %s, %s controls, PRs %s / %s',
                 budget_plan.name, len(budget_plan.budget_control_ids), pr_approved.name, pr_waiting.name)
