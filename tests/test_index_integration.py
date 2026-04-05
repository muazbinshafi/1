import unittest
import socket
import threading
import http.server
import socketserver
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestIndexIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        Handler = http.server.SimpleHTTPRequestHandler
        cls.httpd = socketserver.TCPServer(("", cls.port), Handler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_miladicode_index_rendering(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Avoid external resources blocking load
            page.route('**/*', lambda route: route.abort() if route.request.resource_type in ['font', 'stylesheet', 'script'] and not route.request.url.startswith(f"http://localhost:{self.port}") else route.continue_())

            page.goto(f'http://localhost:{self.port}/index.html', wait_until='domcontentloaded')
            title = page.title()

            # The original index.html has this title based on previous files read
            self.assertIn("MiladiCode", title)
            browser.close()

if __name__ == '__main__':
    unittest.main()
