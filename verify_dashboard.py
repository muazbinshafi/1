import unittest
import subprocess
import time
import socket
import os
import urllib.request
from urllib.error import URLError
from playwright.sync_api import sync_playwright
import db
import collector

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate some mock data so the dashboard isn't empty
        collector.generate_mock_leads()

        # Setup Flask server
        cls.port = get_free_port()
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_process = subprocess.Popen(
            ['python', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        url = f'http://127.0.0.1:{cls.port}/api/stats'
        start_time = time.time()
        while time.time() - start_time < 15:
            try:
                urllib.request.urlopen(url)
                break
            except URLError:
                time.sleep(0.5)
        else:
            cls.server_process.kill()
            raise Exception("Server failed to start")

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_dashboard_loads(self):
        page = self.browser.new_page()

        # Block external resources if needed to speed up tests in restricted environments
        page.route('**/*.{png,jpg,jpeg,svg,woff,woff2}', lambda route: route.abort())
        page.route('https://fonts.googleapis.com/**', lambda route: route.abort())

        page.goto(f'http://127.0.0.1:{self.port}/')

        # Wait for initial data to load via API
        try:
            page.wait_for_selector('#leads-body tr', timeout=10000)
        except Exception:
            self.fail("Dashboard table failed to populate leads within timeout.")

        # Verify title
        self.assertEqual(page.title(), 'Universal Lead Collector')

        # Verify stats cards exist
        total_stat = page.locator('#stat-total').inner_text()
        self.assertTrue(int(total_stat) >= 0)

        # Check that table contains the "Send WhatsApp" button
        whatsapp_btn = page.locator('.btn-whatsapp').first
        self.assertTrue(whatsapp_btn.is_visible())

        # Screenshot verification
        page.screenshot(path="dashboard_verification.png", full_page=True)

    def test_whatsapp_link_generation(self):
        page = self.browser.new_page()
        page.goto(f'http://127.0.0.1:{self.port}/')

        # We need to test the logic that constructs the wa.me link without actually sending one
        # Because window.open is used, we can intercept new pages

        try:
            page.wait_for_selector('#leads-body tr', timeout=10000)
        except Exception:
            self.fail("Table didn't load.")

        # Mock window.open to just log the URL instead of opening it to prevent test hangs/external navigation
        page.evaluate('''() => {
            window.openedUrls = [];
            window.open = function(url, target) {
                window.openedUrls.push(url);
                return null;
            };
        }''')

        # Click the first button
        page.click('.btn-whatsapp:first-child')

        # Give JS a moment to execute
        time.sleep(1)

        # Retrieve the URLs opened
        urls = page.evaluate('window.openedUrls')
        self.assertTrue(len(urls) > 0, "No WhatsApp URL was opened")

        first_url = urls[0]
        self.assertTrue(first_url.startswith('https://wa.me/'), "URL should point to wa.me")

        # We can optionally decode the URL to check the message format
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(first_url)
        params = parse_qs(parsed_url.query)
        self.assertTrue('text' in params, "Message text should be included in wa.me link")
        self.assertTrue('Business Solutions' in params['text'][0])

if __name__ == '__main__':
    unittest.main()
