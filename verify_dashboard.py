import unittest
import subprocess
import time
import socket
import urllib.request
import os
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Remove DB to ensure clean start
        if os.path.exists('leads.db'):
            os.remove('leads.db')

        # Find available port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        # Start server
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(
            ['python3', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        cls.url = f"http://127.0.0.1:{cls.port}"

        # Wait for server to start
        max_retries = 30
        for _ in range(max_retries):
            try:
                urllib.request.urlopen(cls.url)
                break
            except Exception:
                time.sleep(1)
        else:
            cls.server_process.kill()
            raise Exception("Server failed to start")

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_dashboard_loads(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external resources to avoid timeouts in test environment
            page.route("**/*", lambda route: route.continue_() if not ("googleapis" in route.request.url or "cloudflare" in route.request.url) else route.abort())

            page.goto(self.url)

            # Check title
            self.assertIn("Lead Collector", page.title())

            # Wait for JS to populate tables
            try:
                page.wait_for_selector('tr[data-id]', timeout=15000)
            except Exception:
                self.fail("Table failed to populate")

            # Verify mock data exists
            rows = page.locator('tr[data-id]').count()
            self.assertGreater(rows, 0)

            # Click WhatsApp button and verify optimistic UI
            first_row = page.locator('tr[data-id]').first
            btn = first_row.locator('.btn-whatsapp')

            # Intercept new tab (window.open)
            with page.expect_popup() as popup_info:
                btn.click()
            popup = popup_info.value

            # Verify URL contains wa.me or api.whatsapp.com and correct message
            self.assertTrue('whatsapp.com' in popup.url or 'wa.me' in popup.url)
            self.assertTrue('Business Solutions' in urllib.parse.unquote(popup.url))

            # Verify row opacity changed (optimistic update)
            style = first_row.get_attribute('style')
            self.assertIn('opacity: 0.5', style)

            browser.close()

if __name__ == '__main__':
    unittest.main()
