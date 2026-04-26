import unittest
import os
import subprocess
import time
import socket
from playwright.sync_api import sync_playwright
import sqlite3
import collector

class TestIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to open port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        # Start server
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(['python', 'run.py'], env=env)
        time.sleep(2) # Wait for server to start

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.terminate()
        cls.server_process.wait()

    def setUp(self):
        # Reset DB before each test
        if os.path.exists('leads.db'):
            os.remove('leads.db')
        collector.DB_PATH = 'leads.db'
        collector.setup_db()
        collector.generate_mock_leads()

    def test_dashboard_ui(self):
        page = self.browser.new_page()
        page.goto(f'http://localhost:{self.port}/dashboard', wait_until='domcontentloaded')

        # Verify title
        self.assertIn("Universal Lead Collector", page.title())

        # Wait for table to populate
        try:
            page.wait_for_selector('.btn-whatsapp', timeout=5000)
        except Exception as e:
            self.fail(f"Table did not populate: {e}")

        # Verify columns exist
        self.assertTrue(page.locator("text=Business Name").is_visible())
        self.assertTrue(page.locator("text=Type").is_visible())
        self.assertTrue(page.locator("text=Action").is_visible())

        # Count rows
        rows = page.locator("#leads-body tr")
        self.assertGreater(rows.count(), 0)

        page.close()

    def test_whatsapp_button(self):
        context = self.browser.new_context()
        page = context.new_page()
        page.goto(f'http://localhost:{self.port}/dashboard', wait_until='domcontentloaded')

        # Wait for data
        page.wait_for_selector('.btn-whatsapp', timeout=5000)

        # Click first button and catch popup
        with context.expect_page() as new_page_info:
            page.locator('.btn-whatsapp').first.click()

        new_page = new_page_info.value
        try:
            new_page.wait_for_load_state(timeout=5000)
        except Exception:
            pass # Ignore timeout if it gets stuck redirecting

        # Verify it went to wa.me or api.whatsapp.com
        url = new_page.url
        self.assertTrue('wa.me' in url or 'whatsapp.com' in url or 'api.whatsapp.com' in url)

        new_page.close()
        page.close()
        context.close()

if __name__ == '__main__':
    unittest.main()