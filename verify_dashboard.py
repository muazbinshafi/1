import unittest
from playwright.sync_api import sync_playwright
import urllib.request
import subprocess
import time
import socket
import os
import sys

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find available port
        sock = socket.socket()
        sock.bind(('', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        cls.env = os.environ.copy()
        cls.env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in cls.env:
            del cls.env['WERKZEUG_RUN_MAIN']

        cls.server = subprocess.Popen(
            [sys.executable, 'run.py'],
            env=cls.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to be ready
        for _ in range(30):
            try:
                urllib.request.urlopen(f'http://localhost:{cls.port}')
                break
            except Exception:
                time.sleep(1)
        else:
            raise Exception("Server failed to start")

        # Start Playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()
        cls.context = cls.browser.new_context()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.terminate()
        cls.server.wait()

    def test_dashboard_renders(self):
        page = self.context.new_page()
        # Mock external requests to avoid timeouts, but allow whatsapp links
        def route_handler(route):
            url = route.request.url
            if url.startswith("https://") and not ("whatsapp.com" in url or "wa.me" in url):
                route.abort()
            else:
                route.continue_()

        page.route("**/*", route_handler)

        page.goto(f'http://localhost:{self.port}', wait_until='domcontentloaded')

        # Verify title
        self.assertIn("Universal Lead Collector", page.title())

        # Verify stats render
        total = page.locator('#total-leads').inner_text()
        self.assertIsNotNone(total)

        # Generate mock leads to populate DB
        subprocess.run([sys.executable, '-c', 'import collector; collector.generate_mock_leads(); collector.collect_leads()'], env=self.env)

        # Reload to see new leads
        page.goto(f'http://localhost:{self.port}', wait_until='domcontentloaded')

        try:
            # Wait for leads table to populate (background job might take a sec)
            page.wait_for_selector('.btn-whatsapp', timeout=10000)

            # Click WhatsApp button
            with page.expect_popup() as popup_info:
                page.locator('.btn-whatsapp').first.click()

            popup = popup_info.value
            try:
                popup.wait_for_load_state('domcontentloaded', timeout=10000)
            except Exception:
                pass # Accept timeouts here as long as the URL is roughly correct initially

            # wa.me redirects, or it's still at wa.me
            self.assertTrue("whatsapp.com" in popup.url or "api.whatsapp.com" in popup.url or "wa.me" in popup.url)

        except Exception as e:
            self.fail(f"UI interaction failed: {e}")

if __name__ == '__main__':
    unittest.main()
