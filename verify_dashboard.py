import unittest
import socket
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright
import os

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to a free port dynamically
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # Start Flask app
        os.environ['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in os.environ:
            del os.environ['WERKZEUG_RUN_MAIN']

        cls.process = subprocess.Popen(['python3', 'run.py'])

        # Wait for server to start
        for _ in range(30):
            try:
                urllib.request.urlopen(f'http://localhost:{cls.port}')
                break
            except Exception:
                time.sleep(1)
        else:
            cls.process.kill()
            raise Exception("Server failed to start")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.process.kill()
        cls.process.wait()

    def test_dashboard_renders(self):
        page = self.browser.new_page()
        page.goto(f'http://localhost:{self.port}')

        # Wait for stats and leads to load
        try:
            page.wait_for_selector('h1', text='Universal Lead Collector', timeout=5000)
            page.wait_for_selector('.stat-card p', timeout=5000)

            # Since collection can be slow or fall back to mock leads, we'll give it ample time
            page.wait_for_selector('#leads-body tr', timeout=30000)
        except Exception as e:
            print(f"Wait failed, moving on to snapshot: {e}")

        page.screenshot(path='dashboard.png')

        # Check elements
        self.assertTrue(page.is_visible('h1'))

        # Click a WhatsApp button
        with page.expect_popup() as popup_info:
            page.click('.btn-whatsapp')

        popup = popup_info.value
        url = popup.url
        self.assertTrue('whatsapp.com' in url or 'wa.me' in url or 'api.whatsapp.com' in url)

        # Wait a bit for the optimistic UI update and background task
        time.sleep(2)

if __name__ == '__main__':
    unittest.main()
