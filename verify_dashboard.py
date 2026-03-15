import unittest
from playwright.sync_api import sync_playwright
import urllib.request
import time
import os
import subprocess
import signal
import collector

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We start flask app in a separate process
        # Make sure leads.db has some data
        if os.path.exists('leads.db'):
            os.remove('leads.db')

        import run
        run.init_db('leads.db')
        collector.generate_mock_leads('leads.db')

        # Start server
        cls.server_process = subprocess.Popen(["python3", "run.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # wait for it to start
        max_retries = 30
        started = False
        for _ in range(max_retries):
            try:
                urllib.request.urlopen("http://localhost:5000", timeout=1)
                started = True
                break
            except Exception:
                time.sleep(1)

        if not started:
            cls.server_process.kill()
            raise Exception("Server failed to start")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.send_signal(signal.SIGINT)
        cls.server_process.wait()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        # Block external resources if any
        self.page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

    def tearDown(self):
        self.context.close()

    def test_dashboard_loads_and_displays_leads(self):
        self.page.goto("http://localhost:5000")

        # Verify title
        self.assertIn("Universal Lead Collector", self.page.title())

        # Wait for table to populate
        self.page.wait_for_selector("table#leads-table tbody tr", timeout=10000)

        rows = self.page.locator("table#leads-table tbody tr").all()
        self.assertGreater(len(rows), 0, "No leads loaded in the table")

        # Verify first row data
        first_row_text = rows[0].inner_text()
        self.assertIn("Bahawalpur", first_row_text)

        # Click on WhatsApp button - need to mock window.open to test without opening a new tab
        # Instead, intercept new page
        with self.context.expect_page() as new_page_info:
            self.page.locator("text='Send WhatsApp'").first.click()

        new_page = new_page_info.value
        wa_url = new_page.url
        # WhatsApp API redirects from wa.me to api.whatsapp.com
        self.assertTrue("wa.me" in wa_url or "whatsapp.com" in wa_url)
        new_page.close()

        # Check that row is removed after being contacted
        self.page.wait_for_timeout(2000) # Wait for animation / removal
        new_rows = self.page.locator("table#leads-table tbody tr").all()
        self.assertEqual(len(new_rows), len(rows) - 1, "Lead row was not removed after clicking WhatsApp")

        # Take a screenshot for visual verification
        self.page.screenshot(path="dashboard_screenshot.png")

if __name__ == '__main__':
    unittest.main()
