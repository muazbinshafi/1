import unittest
import subprocess
import time
import os
import socket
import urllib.request
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestDashboardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate mock leads for testing if database is empty
        import collector
        collector.generate_mock_leads()

        # Find a free port
        cls.port = get_free_port()

        # Start Flask app in background
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
        cls.base_url = f"http://localhost:{cls.port}"
        started = False
        for _ in range(30):
            try:
                urllib.request.urlopen(cls.base_url)
                started = True
                break
            except Exception:
                time.sleep(1)

        if not started:
            cls.server_process.kill()
            raise Exception("Failed to start Flask server for UI tests")

        # Start playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server_process.terminate()
        cls.server_process.wait(timeout=5)

    def test_dashboard_loads_and_displays_leads(self):
        page = self.browser.new_page()

        # Block external fonts/stylesheets to speed up tests and avoid timeouts
        page.route("**/*.{woff,woff2,ttf}", lambda route: route.abort())
        page.route("**/fonts.googleapis.com/**", lambda route: route.abort())
        page.route("**/cdnjs.cloudflare.com/**", lambda route: route.abort())

        page.goto(self.base_url)

        # Wait for leads table to populate
        try:
            page.wait_for_selector("#leads-body tr[data-id]", timeout=15000)
        except Exception:
            self.fail("Leads table did not populate within timeout")

        # Verify stats are non-zero
        total_leads = page.inner_text("#total-leads")
        self.assertNotEqual(total_leads, "0", "Total leads should not be 0 after mock data generation")

        # Check WhatsApp button exists
        buttons = page.query_selector_all(".send-whatsapp")
        self.assertGreater(len(buttons), 0, "No WhatsApp buttons found")

        # Intercept window.open calls triggered by WhatsApp button
        # Wait for new page event
        with page.expect_popup() as popup_info:
            buttons[0].click()

        popup = popup_info.value
        popup_url = popup.url

        self.assertTrue("wa.me" in popup_url or "whatsapp.com" in popup_url, f"Expected WhatsApp URL, got {popup_url}")

        # Also wait for the row to disappear from optimistic UI update
        # Give it a second
        time.sleep(1)

        # Take a screenshot
        page.screenshot(path="dashboard_verification.png")
        page.close()

if __name__ == '__main__':
    unittest.main()
