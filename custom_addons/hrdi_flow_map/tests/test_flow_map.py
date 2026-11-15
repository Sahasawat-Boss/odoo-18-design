import os
from contextlib import ExitStack
from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import ChromeBrowser

from ..models.hrdi_flow_map import EDGES, NODES


@tagged('post_install', '-at_install')
class TestFlowMapData(TransactionCase):
    def test_edges_reference_existing_nodes(self):
        keys = {n['key'] for n in NODES}
        for src, dst, _label, _kind in EDGES:
            self.assertIn(src, keys)
            self.assertIn(dst, keys)

    def test_get_flow_data(self):
        data = self.env['hrdi.flow.map'].get_flow_data()
        self.assertEqual(len(data['nodes']), len(NODES))
        installed = [n for n in data['nodes'] if n['installed']]
        for node in installed:
            for metric in node['metrics']:
                self.assertIsNotNone(metric['count'], f"{node['key']}: {metric['label']}")


@tagged('post_install', '-at_install')
class TestFlowMapUi(HttpCase):
    browser_size = '1800,1400'

    def test_flow_map_renders(self):
        """เปิดหน้าจอใน headless Chrome: ต้องไม่มี JS error และวาดกล่อง/เส้นเชื่อมครบ"""
        expected_nodes = len(NODES)
        expected_edges = len(EDGES)
        code = f"""
            const nodes = document.querySelectorAll('.o_hrdi_node').length;
            const edges = document.querySelectorAll('.o_hrdi_edge path').length;
            if (nodes !== {expected_nodes} || edges !== {expected_edges}) {{
                console.error(`expected {expected_nodes} nodes / {expected_edges} edges, got ${{nodes}} / ${{edges}}`);
            }} else {{
                console.log('test successful');
            }}
        """
        with ExitStack() as stack:
            if os.environ.get('HRDI_SCREENSHOT'):
                # HRDI_SCREENSHOT=1 -> save a screenshot of the rendered map (see --screenshots dir)
                original = ChromeBrowser._wait_code_ok

                def wait_and_capture(browser, *args, **kwargs):
                    browser.take_screenshot(prefix='hrdi_flow_map_')
                    return original(browser, *args, **kwargs)

                stack.enter_context(patch.object(ChromeBrowser, '_wait_code_ok', wait_and_capture))
            self.browser_js(
                '/odoo/action-hrdi_flow_map.action_hrdi_flow_map',
                code,
                ready="document.querySelectorAll('.o_hrdi_edge path').length > 0",
                login='admin',
            )
