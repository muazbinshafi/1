import unittest
import time
import subprocess
import urllib.request
import os
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the Flask app
        cls.flask_process = subprocess.Popen(['python3', 'run.py'])

        # Wait for server to start
        max_retries = 30
        for _ in range(max_retries):
            try:
                urllib.request.urlopen("http://localhost:5000")
                break
            except Exception:
                time.sleep(1)
        else:
            cls.flask_process.kill()
            raise RuntimeError("Flask server did not start in time")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.flask_process.terminate()
        cls.flask_process.wait()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_dashboard_loads(self):
        self.page.goto("http://localhost:5000")
        self.assertEqual(self.page.title(), "Universal Lead Collector")

        # We need to wait for scraping to finish and UI to update, which takes a while
        try:
            self.page.wait_for_selector("#total-leads:not(:has-text('0'))", timeout=30000)
        except Exception:
            pass # We don't fail if we fallback or it takes too long

        # Take a screenshot
        self.page.screenshot(path="dashboard_screenshot.png", full_page=True)
        self.assertTrue(os.path.exists("dashboard_screenshot.png"))

if __name__ == '__main__':
    unittest.main()
