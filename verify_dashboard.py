import unittest
import urllib.request
import json
import time
from playwright.sync_api import sync_playwright

class TestDashboard(unittest.TestCase):
    def test_api_stats(self):
        # Wait for data collection to maybe populate, or just check the endpoint
        time.sleep(5)
        req = urllib.request.Request('http://127.0.0.1:5000/api/stats')
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertIn('total', data)
            self.assertIn('contacted', data)
            self.assertIn('new', data)

    def test_ui_and_contact(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # Mock window.open so we don't actually open whatsapp and block
            page = context.new_page()
            page.add_init_script("window.open = function(url, target) { window.lastOpenedUrl = url; };")

            page.goto('http://127.0.0.1:5000/')

            # Wait for leads to populate
            page.wait_for_selector('.btn-whatsapp', timeout=15000)

            # Check stats
            total_leads = page.locator('#total-leads').inner_text()
            self.assertGreater(int(total_leads), 0)

            # Click the first whatsapp button
            first_btn = page.locator('.btn-whatsapp').first
            first_btn.click()

            # Give it a moment to process the click and the API call
            time.sleep(2)

            # Check if url was opened
            last_url = page.evaluate("window.lastOpenedUrl")
            self.assertIsNotNone(last_url)
            self.assertIn('wa.me', last_url)

            browser.close()

if __name__ == '__main__':
    unittest.main()
