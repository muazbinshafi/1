import unittest
import urllib.request
import time
import os
from playwright.sync_api import sync_playwright

class TestFrontendVerification(unittest.TestCase):
    def test_dashboard_renders(self):
        url = "http://localhost:5000"

        # Wait up to 5 seconds for the server to start
        max_retries = 5
        for i in range(max_retries):
            try:
                urllib.request.urlopen(url)
                break
            except Exception as e:
                if i == max_retries - 1:
                    self.fail(f"Could not connect to Flask server at {url}: {e}")
                time.sleep(1)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to dashboard
            page.goto(url)

            # Wait for JS to load leads
            page.wait_for_selector("#leads-table-body tr")

            # Check title
            self.assertIn("Universal Lead Collector", page.title())

            # Check stats
            total_leads = page.inner_text("#total-leads")
            self.assertNotEqual(total_leads, "0")

            # Check table contents
            rows = page.locator("#leads-table-body tr").count()
            self.assertGreater(rows, 0)

            # Check button exists
            btn_count = page.locator(".btn-whatsapp").count()
            self.assertGreater(btn_count, 0)

            # Take a screenshot
            page.screenshot(path="dashboard_screenshot.png", full_page=True)
            print("Screenshot saved to dashboard_screenshot.png")

            browser.close()

if __name__ == '__main__':
    unittest.main()