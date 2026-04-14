import unittest
import os
import time
import socket
import threading
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
import run
import collector

class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup testing database
        cls.db_path = 'test_leads_ui.db'
        collector.DB_PATH = cls.db_path
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        collector.init_db()
        collector.generate_mock_leads()

        # Find available port dynamically
        sock = socket.socket()
        sock.bind(('', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        # Start Flask server
        cls.server = make_server('127.0.0.1', cls.port, run.app)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()

        # Playwright setup
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.context = cls.browser.new_context()
        cls.page = cls.context.new_page()

    @classmethod
    def tearDownClass(cls):
        cls.page.close()
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()

        cls.server.shutdown()
        cls.thread.join()

        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_dashboard_load(self):
        self.page.goto(f'http://127.0.0.1:{self.port}')

        # Verify stats load initially
        self.page.wait_for_selector('#total-leads')
        total = self.page.locator('#total-leads').inner_text()
        self.assertEqual(total, '5') # Based on mock data

    def test_whatsapp_button_optimistic_ui(self):
        self.page.goto(f'http://127.0.0.1:{self.port}')

        # Wait for leads table to populate
        self.page.wait_for_selector('table.leads-table tbody tr')

        initial_rows = self.page.locator('table.leads-table tbody tr').count()
        self.assertGreater(initial_rows, 0)

        # Handle popup expectation
        with self.context.expect_page() as new_page_info:
            # Click first send whatsapp button
            self.page.locator('.btn-whatsapp').first.click()

        new_page = new_page_info.value

        # Verify Optimistic UI update (row removed immediately)
        new_rows = self.page.locator('table.leads-table tbody tr').count()
        self.assertEqual(new_rows, initial_rows - 1)

        # Wait for stats to update after backend request finishes
        self.page.wait_for_function('document.getElementById("contacted-leads").innerText === "1"')

        # Verify URL redirection
        self.assertIn('api.whatsapp.com', new_page.url)
        new_page.close()

if __name__ == '__main__':
    unittest.main()
