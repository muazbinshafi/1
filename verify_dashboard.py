import os
import signal
import socket
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright
import sqlite3

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def run_e2e_tests():
    port = get_free_port()

    # Initialize DB with mock data for test
    if os.path.exists('leads.db'):
        os.remove('leads.db')

    import collector
    collector.init_db()
    collector.generate_mock_leads()

    env = os.environ.copy()
    env['PORT'] = str(port)
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    print(f"Starting Flask server on port {port}...")
    server_process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    server_ready = False
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://localhost:{port}/api/stats')
            server_ready = True
            break
        except Exception:
            time.sleep(0.5)

    if not server_ready:
        server_process.kill()
        raise Exception("Server failed to start in time.")

    print("Server ready. Running Playwright verification...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Load dashboard
            page.goto(f"http://localhost:{port}/")
            page.wait_for_selector("#leads-table")

            # Verify UI shows mock data
            total_leads = page.locator("#total-leads").inner_text()
            assert total_leads == "6", f"Expected 6 total leads, got {total_leads}"

            # Find and click WhatsApp button
            wa_button = page.locator(".btn-whatsapp").first
            row = wa_button.locator("xpath=ancestor::tr")
            business_name = row.locator("td").first.inner_text()

            # We need to test the click interaction but prevent actual navigation/new tab
            with context.expect_page() as new_page_info:
                wa_button.click()
            new_page = new_page_info.value

            # Check URL opened
            assert "wa.me/92" in new_page.url or "api.whatsapp.com" in new_page.url, f"Expected WhatsApp URL, got {new_page.url}"
            new_page.close()

            # Optimistic update check: wait a bit, row should be gone
            time.sleep(1)
            remaining_rows = page.locator("#leads-body tr").count()
            assert remaining_rows == 5, f"Expected 5 rows remaining, got {remaining_rows}"

            # Wait for backend update and verify stats changed
            time.sleep(2)
            page.reload()
            page.wait_for_selector("#leads-table")
            contacted_leads = page.locator("#contacted-leads").inner_text()
            assert contacted_leads == "1", f"Expected 1 contacted lead, got {contacted_leads}"

            print("E2E Playwright verification passed successfully.")
            browser.close()

    finally:
        server_process.send_signal(signal.SIGTERM)
        server_process.wait()

if __name__ == "__main__":
    run_e2e_tests()
