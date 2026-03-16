import unittest
from playwright.sync_api import sync_playwright
import database
import urllib.request
import time
import os
import signal
import subprocess

class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'leads.db'
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        # Start server
        cls.server_process = subprocess.Popen(['python3', 'run.py'])
        time.sleep(3) # Wait for startup

        # Populate with mock data via collector script instead of just db calls,
        # so we're sure it matches reality
        import collector
        collector.generate_mock_leads()

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_dashboard_ui(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external fonts
            page.route("**/*.{ttf,woff,woff2}", lambda route: route.abort())
            page.route("**/fonts.googleapis.com/**", lambda route: route.abort())

            page.goto('http://127.0.0.1:5000', timeout=60000)

            # Wait for leads table
            page.wait_for_selector('#leads-body tr', timeout=30000)

            # Verify stats
            total_text = page.locator('#total-leads').inner_text()
            self.assertEqual(total_text, "5")

            # Verify table row
            rows = page.locator('#leads-body tr').all()
            self.assertEqual(len(rows), 5)

            first_row = rows[0]
            action_btn = first_row.locator('.btn-whatsapp')
            self.assertTrue(action_btn.is_visible())

            business_name = first_row.locator('td:nth-child(1)').inner_text()
            business_type = first_row.locator('td:nth-child(2)').inner_text()

            # Take a screenshot
            page.screenshot(path="dashboard_screenshot.png")

            browser.close()

if __name__ == '__main__':
    unittest.main()
