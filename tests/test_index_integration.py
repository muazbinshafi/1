import unittest
import subprocess
import time
import socket
from playwright.sync_api import sync_playwright

class TestIndexIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find available port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # Start local HTTP server
        cls.server_process = subprocess.Popen(['python3', '-m', 'http.server', str(cls.port)])
        time.sleep(2) # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()

    def test_miladi_code_renders(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Route external fonts/scripts to prevent timeout
            page.route('**/*.{woff,woff2,ttf,js}', lambda route: route.abort())
            page.route('https://fonts.googleapis.com/**', lambda route: route.abort())

            response = page.goto(f'http://localhost:{self.port}/index.html', wait_until='domcontentloaded')
            self.assertEqual(response.status, 200)

            title = page.title()
            self.assertIn('MiladiCode', title)

            browser.close()

if __name__ == '__main__':
    unittest.main()
