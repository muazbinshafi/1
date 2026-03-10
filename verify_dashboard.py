import unittest
import urllib.request
import time
import subprocess
from playwright.sync_api import sync_playwright

class TestFrontendDashboard(unittest.TestCase):
    def test_dashboard_loads(self):
        """
        Tests that the frontend dashboard loads and has the correct elements.
        Assumes the Flask server is running locally on port 5000.
        """
        # Ensure server is running before attempting playwright
        try:
            req = urllib.request.Request('http://127.0.0.1:5000/')
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 200)
        except Exception as e:
            self.fail(f"Flask server is not running on port 5000: {e}")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto('http://127.0.0.1:5000/')

            # Check title
            self.assertIn("Universal Lead Collector", page.title())

            # Wait for stats to load
            page.wait_for_selector('.stat-value', state='visible')

            # Take screenshot for verification
            page.screenshot(path="dashboard_screenshot.png")

            # Check for main elements
            self.assertTrue(page.locator('h1').is_visible())
            self.assertTrue(page.locator('#stat-total').is_visible())
            self.assertTrue(page.locator('table').is_visible())

            browser.close()

if __name__ == '__main__':
    unittest.main()
