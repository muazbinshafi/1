import unittest
import threading
import time
import requests
from playwright.sync_api import sync_playwright
import run

class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the Flask app in a separate thread
        cls.flask_thread = threading.Thread(target=lambda: run.app.run(port=5000, use_reloader=False))
        cls.flask_thread.daemon = True
        cls.flask_thread.start()

        # Wait for the app to start
        time.sleep(3)

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_dashboard_loads_and_shows_leads(self):
        page = self.browser.new_page()
        page.goto('http://127.0.0.1:5000/')

        # Wait for leads to load
        page.wait_for_selector('table#leads-table')

        # Ensure that the table rows are present
        rows = page.locator('tbody#leads-body tr').count()
        self.assertGreater(rows, 0, "Dashboard should load at least one mock lead.")

        # Take a screenshot to verify layout
        page.screenshot(path="dashboard_verification.png")

        # Check stat cards exist and are not empty
        total_text = page.locator('#stat-total').inner_text()
        self.assertNotEqual(total_text, "0", "Total stats should be updated.")

    def test_whatsapp_button_hides_lead(self):
        page = self.browser.new_page()
        page.goto('http://127.0.0.1:5000/')

        # Wait for leads to load
        page.wait_for_selector('table#leads-table tbody tr')

        initial_rows = page.locator('tbody#leads-body tr').count()
        self.assertGreater(initial_rows, 0)

        # Override window.open so the test doesn't actually open a new tab and block
        page.evaluate("window.open = function() { return null; }")

        # Click the first WhatsApp button
        page.locator('tbody#leads-body tr').first.locator('button.btn-whatsapp').click()

        # Wait for the row to be removed (animation takes 300ms)
        page.wait_for_timeout(1000)

        final_rows = page.locator('tbody#leads-body tr').count()
        self.assertEqual(final_rows, initial_rows - 1, "The contacted lead should be hidden from the active list.")

if __name__ == '__main__':
    unittest.main()
