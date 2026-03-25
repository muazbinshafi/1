import unittest
import urllib.request
import time
import os
import sys
import sqlite3
import re
from playwright.sync_api import sync_playwright

# Ensure workspace paths are correct for local imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from run import init_db, insert_leads, DB_PATH
import collector

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We assume the Flask app is already running locally at PORT.
        # Check if the server is accessible.
        cls.port = int(os.environ.get('PORT', 5000))
        cls.url = f"http://127.0.0.1:{cls.port}"

        # We need mock data in the DB to test the UI.
        # Make sure the DB exists and has data.
        init_db(DB_PATH)
        mock_leads = collector.generate_mock_leads()
        insert_leads(mock_leads, db_path=DB_PATH)

        # Wait a bit for the server to be ready
        retries = 5
        while retries > 0:
            try:
                urllib.request.urlopen(cls.url)
                break
            except urllib.error.URLError:
                time.sleep(1)
                retries -= 1
        else:
            raise Exception("Flask server is not running or accessible.")

    def setUp(self):
        self.playwright = sync_playwright().start()
        # Use headless true for tests, false if debugging
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def test_dashboard_renders(self):
        self.page.goto(self.url)
        # Verify title
        self.assertEqual(self.page.title(), "Universal Lead Collector")

        # Verify header
        header = self.page.locator('h1').inner_text()
        self.assertEqual(header, "Universal Lead Collector")

        # Verify analytics section exists
        self.assertTrue(self.page.locator('.analytics-section').is_visible())

        # Take a screenshot for verification
        self.page.screenshot(path="dashboard.png")

    def test_leads_table_populates(self):
        self.page.goto(self.url)

        # Wait for the JS fetch to complete and populate the table
        try:
            # We look for a table row that contains a "Send WhatsApp" button
            self.page.wait_for_selector('table tbody tr:has(.btn-whatsapp)', timeout=10000)

            # Check row count
            rows = self.page.locator('table tbody tr').all()
            self.assertGreater(len(rows), 0, "No leads were populated in the table.")

            # Take a screenshot
            self.page.screenshot(path="verification.png")

        except Exception as e:
            self.fail(f"Table did not populate: {e}")

    def test_whatsapp_link_generation(self):
        self.page.goto(self.url)

        # Wait for the table to populate
        try:
            self.page.wait_for_selector('table tbody tr:has(.btn-whatsapp)', timeout=10000)

            # Get the first button
            btn = self.page.locator('table tbody tr .btn-whatsapp').first
            name = btn.get_attribute('data-name')
            phone = btn.get_attribute('data-phone')
            btype = btn.get_attribute('data-type')

            self.assertIsNotNone(name)
            self.assertIsNotNone(phone)
            self.assertIsNotNone(btype)

            # We can't easily test the window.open behavior in playwright without
            # intercepting the new page event, but we can verify the link format indirectly.

            # Intercept new page
            with self.context.expect_page() as new_page_info:
                # Click the button which triggers window.open
                btn.click()

            new_page = new_page_info.value

            # Check if the URL is a whatsapp URL
            url = new_page.url
            self.assertTrue("whatsapp.com" in url or "api.whatsapp.com" in url)

            # Close the new page
            new_page.close()

            # Check if row was optimistically hidden
            # The click event hides the row, but it takes a tiny bit of time
            time.sleep(0.5)
            row = self.page.locator('table tbody tr').first
            # We check if it has style display: none
            style = row.get_attribute('style')
            self.assertTrue(style and "display: none" in style)

        except Exception as e:
            self.fail(f"WhatsApp link test failed: {e}")

if __name__ == '__main__':
    unittest.main()
