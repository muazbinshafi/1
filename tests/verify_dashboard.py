import unittest
import socket
import subprocess
import time
import os
import urllib.request
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate mock leads before starting server
        import collector
        collector.generate_mock_leads()

        # Find free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # Start server with PORT env variable mapped appropriately
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(
            ['python', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to be ready
        url = f'http://127.0.0.1:{cls.port}/api/stats'
        for _ in range(30):
            try:
                urllib.request.urlopen(url)
                break
            except Exception:
                time.sleep(1)
        else:
            cls.server_process.kill()
            raise RuntimeError("Flask server did not start in time.")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.kill()

    def test_dashboard_renders(self):
        page = self.browser.new_page()

        # Route abort for external resources in restricted envs
        page.route('**/*.{png,jpg,jpeg,woff,woff2}', lambda route: route.abort())
        page.route('**/fonts.googleapis.com/**', lambda route: route.abort())
        page.route('**/cdnjs.cloudflare.com/**', lambda route: route.abort())

        page.goto(f'http://127.0.0.1:{self.port}/')

        # Check title
        self.assertEqual(page.title(), 'Universal Lead Collector')

        # Check table columns
        table_headers = page.locator('th').all_text_contents()
        expected_headers = ['Business Name', 'Type', 'City', 'Phone', 'Action']
        self.assertEqual(table_headers, expected_headers)

        # Check stat values
        try:
            page.wait_for_selector('tr[data-id]', timeout=5000)
            new_leads_text = page.locator('#stat-new').inner_text()
            self.assertGreater(int(new_leads_text), 0)

            # Click Whatsapp button
            with page.expect_popup() as popup_info:
                page.locator('.btn-whatsapp').first.click()
            popup = popup_info.value

            # Wait for url redirection or verify URL contains api.whatsapp.com/whatsapp.com
            popup.wait_for_load_state('domcontentloaded')
            self.assertTrue('whatsapp.com' in popup.url or 'wa.me' in popup.url)

            # Wait for optimistic UI update (row removed)
            time.sleep(1)
            updated_new_leads_text = page.locator('#stat-new').inner_text()
            self.assertEqual(int(updated_new_leads_text), int(new_leads_text) - 1)

            # Take a screenshot
            page.screenshot(path='verification.png')

        except Exception as e:
            self.fail(f"Dashboard functionality test failed: {e}")

        page.close()

if __name__ == '__main__':
    unittest.main()
