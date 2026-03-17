import unittest
from playwright.sync_api import sync_playwright
import subprocess
import time
import os
import urllib.request
import urllib.error

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate mock leads before starting the app to ensure data is present
        import collector
        collector.generate_mock_leads()

        # Start Flask app
        cls.flask_process = subprocess.Popen(['python3', 'run.py'])

        # Wait for Flask to start
        cls.url = "http://localhost:5000/"
        started = False
        for _ in range(30):
            try:
                urllib.request.urlopen(cls.url)
                started = True
                break
            except urllib.error.URLError:
                time.sleep(1)

        if not started:
            cls.flask_process.kill()
            raise Exception("Flask server failed to start")

    @classmethod
    def tearDownClass(cls):
        cls.flask_process.terminate()
        cls.flask_process.wait()

    def test_dashboard_elements(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external requests that might timeout
            page.route("**/*", lambda route: route.continue_() if not "fonts.googleapis.com" in route.request.url else route.abort())

            page.goto(self.url)

            # Verify titles
            self.assertEqual(page.title(), "Universal Lead Collector")
            self.assertTrue(page.locator("h1:has-text('Universal Lead Collector')").is_visible())

            # Verify stats boxes
            self.assertTrue(page.locator("h3:has-text('Total Leads')").is_visible())

            # Verify table populates
            try:
                # Wait for the table to have rows. The initial scrape/mock might take a moment.
                page.wait_for_selector("#leads-body tr", timeout=15000)
            except Exception as e:
                self.fail(f"Table failed to populate within 15 seconds: {e}")

            # Verify row content
            row = page.locator("#leads-body tr").first
            self.assertTrue(row.is_visible())
            self.assertTrue(row.locator("td").count() > 0)

            # Verify WhatsApp button exists
            btn = row.locator("button.whatsapp-btn")
            self.assertTrue(btn.is_visible())

            browser.close()

if __name__ == '__main__':
    unittest.main()
