import unittest
import subprocess
import time
import os
import socket
from playwright.sync_api import sync_playwright

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # find free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        cls.port = s.getsockname()[1]
        s.close()

        # set up mock data
        import collector
        collector.generate_mock_leads()

        # Start server
        env = os.environ.copy()
        env['PORT'] = str(cls.port)
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']

        cls.server_proc = subprocess.Popen(['python3', 'run.py'], env=env)

        # Wait for server
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        cls.server_proc.wait()

    def test_dashboard_loads_and_displays_data(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(f"http://localhost:{self.port}", timeout=10000)

                # Check title
                self.assertIn("Universal Lead Collector", page.title())

                # Wait for table
                page.wait_for_selector("#leads-body tr")

                # Count rows
                rows = page.locator("#leads-body tr")
                self.assertGreater(rows.count(), 0)

                # Check button
                btn = page.locator(".btn-whatsapp").first
                self.assertIsNotNone(btn)

            except Exception as e:
                self.fail(f"Test failed: {e}")
            finally:
                browser.close()

if __name__ == '__main__':
    unittest.main()
