{
    'name': 'HRDI Home',
    'version': '18.0.1.0.0',
    'summary': 'หน้าแรกของระบบ HRDI: งานของฉัน, เริ่มงานด่วน, ทางเข้าระบบงาน และผัง Flow',
    'category': 'Productivity',
    'author': 'HRDI ERP Project',
    'license': 'LGPL-3',
    # depend แค่ web: ทางลัดไปแอปที่ยังไม่ติดตั้งจะถูกซ่อนเอง
    'depends': ['web'],
    'data': [
        'views/hrdi_home_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hrdi_home/static/src/**/*',
        ],
    },
    # ตั้งหน้านี้เป็น Home Action ของผู้ใช้ภายใน (login แล้วเข้าหน้านี้ทันที)
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'application': True,
    'installable': True,
}
