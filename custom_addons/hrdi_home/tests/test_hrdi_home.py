import os
from contextlib import ExitStack
from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import ChromeBrowser


@tagged('post_install', '-at_install')
class TestHrdiHomeData(TransactionCase):
    def test_admin_lands_on_hrdi_home(self):
        # action_id is an ir.actions.actions record; compare ids, not the (client) action record itself
        self.assertEqual(self.env.ref('base.user_admin').action_id.id, self.env.ref('hrdi_home.action_hrdi_home').id)

    def test_home_data(self):
        data = self.env['hrdi.home'].get_home_data()
        self.assertTrue(data['todos'])
        self.assertTrue(data['quick_actions'])
        self.assertTrue(data['sections'])
        for todo in data['todos']:
            self.assertIsInstance(todo['count'], int, todo['key'])

    def test_hrdi_menu_before_flow(self):
        home = self.env.ref('hrdi_home.menu_hrdi_home_root')
        flow = self.env.ref('hrdi_flow_map.menu_hrdi_flow_map_root', raise_if_not_found=False)
        if flow:
            self.assertLess(home.sequence, flow.sequence)


@tagged('post_install', '-at_install')
class TestHrdiHomeUi(HttpCase):
    browser_size = '1600,1100'

    def test_login_opens_hrdi_home(self):
        """เปิด /odoo หลัง login: ต้องเข้าหน้า HRDI Home ทันที และไม่มี JS error"""
        code = """
            const todos = document.querySelectorAll('.o_hrdi_home .o_hrdi_todo').length;
            const quicks = document.querySelectorAll('.o_hrdi_home .o_hrdi_quick').length;
            if (!todos || !quicks) {
                console.error(`home not rendered: ${todos} todos / ${quicks} quick actions`);
            } else {
                console.log('test successful');
            }
        """
        with ExitStack() as stack:
            if os.environ.get('HRDI_SCREENSHOT'):
                original = ChromeBrowser._wait_code_ok

                def wait_and_capture(browser, *args, **kwargs):
                    browser.take_screenshot(prefix='hrdi_home_')
                    return original(browser, *args, **kwargs)

                stack.enter_context(patch.object(ChromeBrowser, '_wait_code_ok', wait_and_capture))
            self.browser_js('/odoo', code, ready="!!document.querySelector('.o_hrdi_home .o_hrdi_todo')", login='admin')
