import unittest
from playwright.sync_api import sync_playwright

class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.context = cls.browser.new_context()
        cls.page = cls.context.new_page()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_dashboard_loads(self):
        self.page.goto("http://localhost:5000")
        self.assertIn("Business Solutions Lead Dashboard", self.page.content())
        self.page.wait_for_selector("#leads-body tr", timeout=5000)

        # Take a screenshot
        self.page.screenshot(path="dashboard_screenshot.png")

        # Check that there is at least one row
        rows = self.page.locator("#leads-body tr").count()
        self.assertGreater(rows, 0, "No leads loaded in the dashboard")

if __name__ == "__main__":
    unittest.main()
