import unittest
from playwright.sync_api import sync_playwright
import urllib.request
import time
import subprocess
import os
import signal
import collector

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to start the Flask server in a subprocess
        # Create some mock data first
        if os.path.exists('leads.db'):
            os.remove('leads.db')
        collector.init_db()
        collector.generate_mock_leads()

        # Start server with custom PORT
        env = os.environ.copy()
        env['PORT'] = '5001'
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(
            ['python', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # Wait for server to start
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        if cls.server_process:
            os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)

        if os.path.exists('leads.db'):
            os.remove('leads.db')

    def test_dashboard_ui(self):
        with sync_playwright() as p:
            # We want to block external requests that may timeout
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            # Navigate to local server
            page.goto('http://127.0.0.1:5001', timeout=10000)

            # Wait for table to load
            try:
                page.wait_for_selector('#leads-body tr td', timeout=5000)
            except Exception as e:
                self.fail(f"Table didn't load: {e}")

            # Verify stats
            total = page.locator('#stat-total').inner_text()
            self.assertNotEqual(total, "0")

            # Find a WhatsApp button
            buttons = page.locator('.btn-whatsapp')
            self.assertGreater(buttons.count(), 0)

            # We don't click it since it opens a new tab, just verify it exists

            browser.close()

if __name__ == '__main__':
    unittest.main()
