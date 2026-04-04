import unittest
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

class TestIndexIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start a simple HTTP server to serve the portfolio index.html
        cls.port = 8000
        handler = http.server.SimpleHTTPRequestHandler
        cls.httpd = socketserver.TCPServer(("", cls.port), handler)

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
        cls.httpd.server_close()
        cls.server_thread.join()

    def test_index_page(self):
        page = self.browser.new_page()
        page.goto(f"http://localhost:{self.port}/index.html", wait_until="domcontentloaded")

        # Verify title
        title = page.title()
        self.assertIn("MiladiCode", title)

if __name__ == '__main__':
    unittest.main()
