import unittest
import urllib.request
import time
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Wait a moment to ensure Flask server is running
        time.sleep(2)

        # Verify server is accessible
        try:
            req = urllib.request.Request('http://127.0.0.1:5000/')
            with urllib.request.urlopen(req) as response:
                cls.server_up = response.status == 200
        except Exception:
            cls.server_up = False

    def test_dashboard_loads_and_displays_data(self):
        if not self.server_up:
            self.skipTest("Flask server is not running on http://127.0.0.1:5000")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Block external resources if needed to speed up / avoid hangs
            # page.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "xhr", "fetch"] else route.abort())

            try:
                page.goto("http://127.0.0.1:5000/")

                # Check Header
                self.assertTrue(page.locator("h1:has-text('Universal Lead Collector')").is_visible())

                # Wait for API fetch
                page.wait_for_selector("#stat-total")

                # Stats should have numbers
                total_text = page.locator("#stat-total").inner_text()
                self.assertTrue(total_text.isdigit())

                # Check if leads loaded
                page.wait_for_selector("#leads-table")

                # Take screenshot
                page.screenshot(path="dashboard_screenshot.png")
            except Exception as e:
                self.fail(f"Playwright test failed: {e}")
            finally:
                browser.close()

if __name__ == '__main__':
    unittest.main()
