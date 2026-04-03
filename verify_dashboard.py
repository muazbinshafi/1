import unittest
import subprocess
import time
import socket
import os
import urllib.request
import json
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup mock db
        os.system('python3 -c "import collector; collector.init_db(); collector.generate_mock_leads()"')

        # Find available port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # Set PORT env var
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.flask_process = subprocess.Popen(['python3', 'run.py'], env=env)

        # Wait for server to start
        max_retries = 10
        for i in range(max_retries):
            try:
                urllib.request.urlopen(f'http://localhost:{cls.port}/api/stats', timeout=1)
                break
            except Exception:
                time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.flask_process.terminate()

    def test_dashboard_loads_and_displays_leads(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(f'http://localhost:{self.port}/')

            # Wait for table to populate
            try:
                page.wait_for_selector('#leads-body tr', timeout=5000)
            except Exception:
                pass

            rows = page.locator('#leads-body tr').count()
            self.assertGreater(rows, 0, "No leads loaded in the table")

            # Check for whatsapp button
            whatsapp_buttons = page.locator('.btn-whatsapp').count()
            self.assertGreater(whatsapp_buttons, 0, "No WhatsApp buttons found")

            browser.close()

if __name__ == '__main__':
    unittest.main()
