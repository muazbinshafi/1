import unittest
import urllib.request
import threading
import socket
import http.server
import socketserver
from playwright.sync_api import sync_playwright

class TestIndexIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find an open port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        Handler = http.server.SimpleHTTPRequestHandler
        cls.httpd = socketserver.TCPServer(("", cls.port), Handler)

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.httpd.shutdown()

    def test_portfolio_page(self):
        page = self.browser.new_page()
        # Wait until domcontentloaded to avoid timeouts on missing assets
        page.goto(f"http://127.0.0.1:{self.port}/index.html", wait_until="domcontentloaded", timeout=10000)

        self.assertIn("MiladiCode", page.title())
        page.close()

if __name__ == '__main__':
    unittest.main()
