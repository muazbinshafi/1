import unittest
from playwright.sync_api import sync_playwright
import subprocess
import socket
import os
import sys
import time
import urllib.request

class TestIndexIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find available port
        sock = socket.socket()
        sock.bind(('', 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        # Start simple HTTP server in project root
        cls.server = subprocess.Popen(
            [sys.executable, '-m', 'http.server', str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server
        for _ in range(30):
            try:
                urllib.request.urlopen(f'http://localhost:{cls.port}')
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise Exception("HTTP Server failed to start")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()
        cls.context = cls.browser.new_context()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.terminate()
        cls.server.wait()

    def test_index_rendering(self):
        page = self.context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.url.startswith("https://") else route.continue_())

        page.goto(f'http://localhost:{self.port}/index.html', wait_until='domcontentloaded')

        self.assertEqual(page.title(), "MiladiCode - Creative Developer")

if __name__ == '__main__':
    unittest.main()
