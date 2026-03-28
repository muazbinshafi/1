import socket
import subprocess
import time
import os
import unittest
from playwright.sync_api import sync_playwright
import urllib.request
import collector

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prepare DB
        cls.db_path = "leads.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        collector.init_db(cls.db_path)
        # Populate with mock data specifically for test
        collector.generate_mock_leads(cls.db_path)

        cls.port = get_free_port()
        env = os.environ.copy()
        env["PORT"] = str(cls.port)
        if "WERKZEUG_RUN_MAIN" in env:
            del env["WERKZEUG_RUN_MAIN"]

        cls.server_process = subprocess.Popen(['python3', 'run.py'], env=env)

        # Wait for server to start
        url = f"http://127.0.0.1:{cls.port}/api/stats"
        for _ in range(15):
            try:
                urllib.request.urlopen(url)
                break
            except Exception:
                time.sleep(1)

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.terminate()
        cls.server_process.wait()

        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_dashboard_renders(self):
        page = self.browser.new_page()
        page.goto(f"http://127.0.0.1:{self.port}/")

        # Verify title
        self.assertIn("Universal Lead Collector", page.title())

        # Wait for table to populate
        page.wait_for_selector("#leads-table tbody tr", timeout=10000)

        # Verify stats updated
        total = page.locator("#total-stat").inner_text()
        self.assertNotEqual(total, "0")

        # Verify WhatsApp button is present
        btn = page.locator(".whatsapp-btn").first
        self.assertTrue(btn.is_visible())

        page.screenshot(path="dashboard.png")

if __name__ == "__main__":
    unittest.main()
