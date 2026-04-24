import unittest
import os
import time
import socket
import threading
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
import run
import collector

class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

class TestIndexE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'test_leads_e2e.db'
        collector.DB_PATH = cls.db_path

        # Disable background jobs for testing
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        collector.setup_db(cls.db_path)
        collector.generate_mock_leads(cls.db_path)

        # Find available port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        run.app.config['TESTING'] = True
        cls.server = ServerThread(run.app, cls.port)
        cls.server.start()
        time.sleep(1) # wait for server to start

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.join()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.context = self.browser.new_context()

        # Block external resources to prevent timeouts during testing
        def route_handler(route):
            if route.request.url.startswith(f"http://127.0.0.1:{self.port}"):
                route.continue_()
            elif "whatsapp.com" in route.request.url or "wa.me" in route.request.url:
                route.continue_()
            else:
                route.abort()

        self.context.route("**/*", route_handler)
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_dashboard_ui(self):
        self.page.goto(f"http://127.0.0.1:{self.port}/", wait_until='domcontentloaded')

        # Wait for leads to load
        try:
            self.page.wait_for_selector("#leads-table tbody tr", timeout=5000)
        except Exception:
            pass # might have loaded fast or slow

        # Check rows
        rows = self.page.locator("#leads-table tbody tr")
        self.assertEqual(rows.count(), 3)

        # Check stats
        total_leads = self.page.locator("#total-leads").inner_text()
        self.assertEqual(total_leads, "3")

        # Click first WhatsApp button
        with self.context.expect_page() as new_page_info:
            rows.nth(0).locator(".btn-whatsapp").click()

        # Close popup
        new_page_info.value.close()

        # Verify optimistic update
        self.page.wait_for_function('document.querySelectorAll("#leads-table tbody tr").length === 2')
        self.assertEqual(self.page.locator("#total-leads").inner_text(), "2")
        self.assertEqual(self.page.locator("#contacted-leads").inner_text(), "1")

if __name__ == '__main__':
    unittest.main()
