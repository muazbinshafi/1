import unittest
from playwright.sync_api import sync_playwright
import urllib.request
import time
import os

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need the Flask app running for this.
        # Ensure server is running and accessible
        server_running = False
        for _ in range(10):
            try:
                urllib.request.urlopen("http://localhost:5000", timeout=1)
                server_running = True
                break
            except Exception:
                time.sleep(1)

        if not server_running:
            raise Exception("Flask server is not running on port 5000. Please start it before running this test.")

    def test_dashboard_renders(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Navigate to dashboard
            page.goto("http://localhost:5000")

            # Wait for content to load via JS
            page.wait_for_selector(".stat-card h3", state="visible")

            # Verify Header
            header_text = page.locator("h1").inner_text()
            self.assertEqual(header_text, "Universal Lead Collector")

            # Verify Analytics section
            stat_cards = page.locator(".stat-card").all()
            self.assertEqual(len(stat_cards), 3)
            self.assertIn("Total Leads", stat_cards[0].inner_text())
            self.assertIn("Contacted", stat_cards[1].inner_text())
            self.assertIn("New Uncontacted", stat_cards[2].inner_text())

            # Take a screenshot
            page.screenshot(path="dashboard_screenshot.png")

            # Verify Table
            table_headers = page.locator("th").all()
            headers_text = [th.inner_text() for th in table_headers]
            self.assertListEqual(headers_text, ["Business Name", "Type", "City", "Phone", "Action"])

            # Check for leads
            rows = page.locator("#leads-body tr").all()

            if len(rows) > 0 and rows[0].get_attribute("data-id") is not None:
                # We have actual leads, test WhatsApp button
                whatsapp_button = rows[0].locator("a[data-action='contact']")
                self.assertTrue(whatsapp_button.is_visible())
                self.assertEqual(whatsapp_button.inner_text(), "Send WhatsApp")

                # Verify URL format contains wa.me and encoded text
                href = whatsapp_button.get_attribute("href")
                self.assertIn("wa.me/", href)
                self.assertIn("text=", href)
                self.assertIn("Business%20Solutions", href) # basic url encoding check

            browser.close()

if __name__ == '__main__':
    unittest.main()