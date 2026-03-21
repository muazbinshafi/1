import unittest
import socket
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright
import os
import signal

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to a free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        # Start Flask app
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

        # Wait for server
        for _ in range(10):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{cls.port}')
                break
            except Exception:
                time.sleep(1)

        # Pre-seed db to avoid waiting for scraper
        subprocess.run(['python', '-c', "import collector; collector.generate_mock_leads()"])

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.server_process.pid, signal.SIGTERM)
        cls.server_process.wait()

    def test_dashboard_ui(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Block external requests for speed in CI
            # Block external requests for speed in CI
            page.route("**/*", lambda route: route.continue_() if not any(x in route.request.url for x in ["fonts.googleapis.com", "cdnjs.cloudflare.com"]) else route.abort())

            page.goto(f'http://127.0.0.1:{self.port}')

            # Wait for data fetch
            try:
                page.wait_for_selector('tr[data-id]', timeout=5000)
                # Wait briefly for stats to update in the UI after fetch
                time.sleep(2)
            except Exception:
                pass # If it times out, we'll assert below anyway

            # Verify stats
            total = page.locator('#stat-total').inner_text()
            self.assertTrue(int(total) > 0)

            # Click WhatsApp button and check new page (whatsapp url)
            with context.expect_page() as new_page_info:
                page.locator('.btn-whatsapp').first.click()

            new_page = new_page_info.value
            new_page.wait_for_load_state('domcontentloaded')
            self.assertTrue("whatsapp.com" in new_page.url or "wa.me" in new_page.url)

            # Back to main page, check row was removed optimistically
            rows = page.locator('tr[data-id]').count()
            self.assertTrue(rows < int(total))

            # Take screenshot
            page.screenshot(path="dashboard.png")

            browser.close()

if __name__ == '__main__':
    unittest.main()
