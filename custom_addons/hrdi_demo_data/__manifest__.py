{
    'name': 'HRDI Demo Data',
    'version': '18.0.1.0.0',
    'summary': 'ข้อมูลตัวอย่างชุดเล็ก: หน่วยงาน, แผนงบ/คุมงบ, ใบขอซื้อที่กันงบจริง',
    'category': 'Hidden',
    'author': 'HRDI ERP Project',
    'license': 'LGPL-3',
    # ใช้ budget period / template ของ demo budget_control (FY2026)
    'depends': ['budget_control_purchase_request'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
