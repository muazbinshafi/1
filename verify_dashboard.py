import unittest
import subprocess
import time
import socket
import os
import urllib.request
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate some mock data for the test UI to look right
        import db
        import collector
        db.init_db()
        collector.generate_mock_leads()

        # Start the Flask app
        cls.port = get_free_port()
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for server to start
        url = f'http://127.0.0.1:{cls.port}'
        max_retries = 10
        for _ in range(max_retries):
            try:
                urllib.request.urlopen(url)
                break
            except Exception:
                time.sleep(1)
        else:
            raise Exception("Flask server failed to start")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'server'):
            cls.server.terminate()
            cls.server.wait()

    def test_dashboard_load_and_data(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Navigate to dashboard
            page.goto(f'http://127.0.0.1:{self.port}')

            # Verify Header
            self.assertEqual(page.title(), 'Universal Lead Collector')
            self.assertTrue(page.locator("h1:has-text('Universal Lead Collector')").is_visible())

            # Wait for data to populate (polling takes time or immediate upon load)
            try:
                page.wait_for_selector(".btn-whatsapp", timeout=5000)
            except Exception:
                pass # If it times out, we assert below anyway

            # Verify stats are no longer zero (mock data has 6 items)
            # It might take a moment, retry if needed
            total = page.locator('#total-leads-count').inner_text()
            if total == '0':
                time.sleep(2) # brief wait for polling to complete
                total = page.locator('#total-leads-count').inner_text()

            self.assertTrue(int(total) > 0)

            # Screenshot
            page.screenshot(path="verification.png", full_page=True)
            browser.close()

if __name__ == '__main__':
    unittest.main()