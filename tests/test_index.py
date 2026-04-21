import unittest
import subprocess
import time
import os
from playwright.sync_api import sync_playwright

class TestE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = os.environ.copy()
        if 'WERKZEUG_RUN_MAIN' in cls.env:
            del cls.env['WERKZEUG_RUN_MAIN']
        cls.env['PORT'] = '5003'

        # We need to make sure we clear the db and the scheduler doesn't immediately overwrite with mock leads if it runs fast
        cls.db_path = 'leads.db'
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        subprocess.run(['python3', '-c', 'import collector; collector.init_db("leads.db"); collector.insert_lead("Test E2E Clinic", "Clinic", "Bahawalpur", "0300-5555555", "leads.db")'])

        cls.server_process = subprocess.Popen(['python3', 'run.py'], env=cls.env)
        time.sleep(3) # wait for server and scheduler startup

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.terminate()

    def test_dashboard_ui_and_whatsapp_link(self):
        page = self.browser.new_page()

        # Block external requests except what's needed for the popup
        def route_interceptor(route, request):
            if "127.0.0.1" in request.url or "wa.me" in request.url or "whatsapp.com" in request.url:
                route.continue_()
            else:
                route.abort()

        page.route("**/*", route_interceptor)
        page.goto('http://127.0.0.1:5003/')

        # Check title
        self.assertEqual(page.title(), 'Universal Lead Collector')

        # Wait for table to populate
        page.wait_for_selector('.leads-table tbody tr', timeout=10000)

        # Filter for the specific row we care about
        row = page.locator('.leads-table tbody tr', has_text='Test E2E Clinic').first
        self.assertTrue(row.is_visible())

        # Intercept the new tab opened by window.open
        with page.expect_popup() as popup_info:
            row.locator('.btn-whatsapp').click()

        popup = popup_info.value
        try:
            popup.wait_for_load_state('domcontentloaded', timeout=5000)
        except Exception:
            pass # Gracefully handle timeout on popup load

        url = popup.url
        self.assertTrue('wa.me/923005555555' in url or 'api.whatsapp.com' in url or 'whatsapp.com' in url)

        # Optimistic UI check
        time.sleep(1) # wait for UI update
        self.assertFalse(row.is_visible())

        popup.close()
        page.close()

if __name__ == '__main__':
    unittest.main()
