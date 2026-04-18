import unittest
import threading
import time
import socket
from playwright.sync_api import sync_playwright
import run
import collector

class TestIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'test_leads_api.db'
        collector.DB_PATH = cls.db_path

        # Free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        cls.app_thread = threading.Thread(target=run.app.run, kwargs={'port': cls.port, 'use_reloader': False, 'debug': False})
        cls.app_thread.daemon = True
        cls.app_thread.start()

        # Wait for server to start
        time.sleep(1)

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        import os
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.generate_mock_leads(self.db_path)
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def test_dashboard_load(self):
        self.page.goto(f'http://localhost:{self.port}/', wait_until='domcontentloaded')

        # Ensure title
        self.assertEqual(self.page.title(), 'Universal Lead Collector')

        # Wait for leads to populate
        try:
            self.page.wait_for_selector('table tbody tr', timeout=5000)
        except Exception:
            self.fail("Leads table did not populate in time")

        rows = self.page.locator('table tbody tr').count()
        self.assertTrue(rows > 0)

        # Click send whatsapp
        with self.page.expect_popup() as popup_info:
            self.page.locator('.btn-whatsapp').first.click()
        popup = popup_info.value

        # Wait for optimistic UI update
        time.sleep(1)
        new_rows = self.page.locator('table tbody tr').count()
        self.assertEqual(new_rows, rows - 1)
        popup.close()

if __name__ == '__main__':
    unittest.main()
