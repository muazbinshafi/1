import unittest
from playwright.sync_api import sync_playwright

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_dashboard_loads_and_displays_stats(self):
        self.page.goto('http://localhost:5000/')
        self.page.wait_for_selector('h1:has-text("Universal Lead Collector")')

        # Take a screenshot to verify layout
        self.page.screenshot(path="dashboard_screenshot.png")

        # Verify stat boxes exist
        total = self.page.locator('#total-leads')
        self.assertTrue(total.is_visible())

if __name__ == '__main__':
    unittest.main()