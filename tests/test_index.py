import unittest
import os
import time
import socket
import subprocess
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestIndexE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        env = os.environ.copy()
        if 'WERKZEUG_RUN_MAIN' in env:
            del env['WERKZEUG_RUN_MAIN']
        env['PORT'] = str(cls.port)
        # Avoid running tests in the existing db, force test db
        env['PYTHONPATH'] = os.path.abspath('.')

        # Populate initial test db
        subprocess.run(['python3', '-c', 'import collector; collector.DB_PATH="test_leads_e2e.db"; collector.generate_mock_leads()'], env=env)

        # We'll mock the DB_PATH in the run.py via a small wrapper if needed,
        # or rely on the actual leads.db for E2E if preferred.
        # To strictly use test_leads_e2e.db, we would need to inject it into run.py environment.
        # For simplicity of E2E, we can let it run normally, just test the UI.

        cls.process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2) # Wait for server

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.process.terminate()
        cls.process.wait()

    def test_dashboard_loads(self):
        page = self.browser.new_page()
        page.goto(f'http://localhost:{self.port}/dashboard')
        self.assertIn("Universal Lead Collector", page.title())

        # Wait for leads to populate
        try:
            page.wait_for_selector('.btn-whatsapp', timeout=10000)
            btn_count = page.locator('.btn-whatsapp').count()
            self.assertGreater(btn_count, 0)
        except Exception as e:
            self.fail(f"Leads did not load: {e}")

if __name__ == '__main__':
    unittest.main()