import unittest
import urllib.request
import threading
import time
import socket
from werkzeug.serving import make_server
from run import app
from playwright.sync_api import sync_playwright

class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find an open port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        cls.server = make_server('127.0.0.1', cls.port, app)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.start()

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server_thread.join()

    def test_dashboard_loads(self):
        page = self.browser.new_page()
        page.goto(f"http://127.0.0.1:{self.port}/")

        # Verify title
        self.assertIn("Universal Lead Collector", page.title())

        # Wait for stats to load
        page.wait_for_selector("#total-leads", timeout=5000)

        # Take screenshot for verification if needed
        # page.screenshot(path="dashboard_loaded.png")
        page.close()

if __name__ == '__main__':
    unittest.main()
