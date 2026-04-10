import os
import unittest
import socket
import urllib.request
import time
import subprocess
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find available port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # Start server
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(
            ['python', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        cls.url = f'http://localhost:5000/'
        max_retries = 30
        for _ in range(max_retries):
            try:
                urllib.request.urlopen(cls.url)
                break
            except urllib.error.URLError:
                time.sleep(1)
        else:
            cls.server_process.terminate()
            raise RuntimeError("Server failed to start")

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_dashboard_renders_and_whatsapp_link(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(self.url)

            # Wait for table to populate
            try:
                page.wait_for_selector('#leads-body tr:not(:has-text("Loading leads..."))', timeout=15000)
            except Exception:
                pass # Continue to let assertions handle failure

            # Verify UI elements
            self.assertTrue(page.locator("h1:has-text('Universal Lead Collector')").is_visible())
            self.assertTrue(page.locator(".stat-card:has-text('Total Leads')").is_visible())

            # Check for WhatsApp button and extract link
            wa_button = page.locator(".whatsapp-btn").first
            if wa_button.is_visible():
                # We can't easily test actual clicking a target="_blank" without handling new pages,
                # but we can verify the dataset structure has been parsed correctly.
                lead_data = wa_button.get_attribute("data-lead")
                self.assertIn("phone", lead_data)

            browser.close()

if __name__ == '__main__':
    unittest.main()
