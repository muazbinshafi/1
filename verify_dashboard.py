import time
import socket
import subprocess
import os
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_test():
    port = get_free_port()

    import sys
    # Start the Flask app
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['TESTING'] = 'true'
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']
    server_process = subprocess.Popen([sys.executable, 'run.py'], env=env)

    # Wait for server to start
    time.sleep(2)

    # Populate mock data directly
    import collector
    collector.init_db()
    collector.generate_mock_leads()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Go to dashboard
            page.goto(f"http://localhost:{port}")

            # Wait for leads table to populate (initial UI logic might take a moment)
            try:
                page.wait_for_selector('table.leads-table tbody tr td', timeout=10000)
            except Exception as e:
                print("Could not wait for leads table to populate. Attempting to proceed.")

            # Verify basic stats
            total = page.locator('#stat-total').inner_text()
            print(f"Total leads: {total}")
            assert int(total) > 0, "No leads were populated."

            # Find the first WhatsApp button
            wa_button = page.locator('.btn-whatsapp').first
            btn_text = wa_button.inner_text()
            print(f"Button text: {btn_text}")

            # Intercept new page for the WhatsApp redirection
            with context.expect_page() as new_page_info:
                wa_button.click()

            new_page = new_page_info.value
            try:
                new_page.wait_for_load_state()
            except Exception:
                pass # Timeout expected for some external links when headless

            url = new_page.url
            print(f"Redirect URL: {url}")
            assert 'api.whatsapp.com' in url or 'wa.me' in url or 'whatsapp.com' in url, f"Unexpected URL: {url}"

            # Give UI time to update
            time.sleep(2)

            # The row should have been removed
            print("Successfully verified UI interaction and WhatsApp redirection.")
            browser.close()

    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_test()
