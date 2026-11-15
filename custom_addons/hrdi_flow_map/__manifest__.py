{
    'name': 'HRDI Flow Map',
    'version': '18.0.1.0.0',
    'summary': 'แผนผังภาพรวม: ขาย→รับเงิน, งบประมาณ, ซื้อ→จ่าย, พัสดุ/ครุภัณฑ์ → GL พร้อมจำนวนเอกสารจริง',
    'category': 'Accounting',
    'author': 'HRDI ERP Project',
    'license': 'LGPL-3',
    # ตั้งใจ depend แค่ web: ถ้าบางแอปยังไม่ติดตั้ง กล่องนั้นจะแสดงเป็นสีเทา แทนที่จะติดตั้งไม่ได้
    'depends': ['web'],
    'data': [
        'views/hrdi_flow_map_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hrdi_flow_map/static/src/**/*',
        ],
    },
    'application': True,
    'installable': True,
}
