import os
import subprocess
import time
import socket
import urllib.request
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url)
            return True
        except Exception:
            time.sleep(0.5)
    return False

def run_verification():
    port = get_free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    # Generate mock leads before running so it's not empty
    os.system('python -c "import collector; collector.init_db(); collector.generate_mock_leads()"')

    print(f"Starting server on port {port}...")
    server_process = subprocess.Popen(['python', 'run.py'], env=env)

    url = f"http://127.0.0.1:{port}/"
    if not wait_for_server(url):
        print("Server failed to start")
        server_process.kill()
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external requests except what we need to speed up tests
            page.route("**/*", lambda route: route.continue_() if not route.request.url.startswith('https://wa.me') else route.abort())

            print("Navigating to dashboard...")
            page.goto(url)
            page.wait_for_selector('.leads-table', timeout=10000)

            # Wait for leads to populate via JS fetch
            try:
                page.wait_for_selector('.btn-whatsapp', timeout=10000)
            except Exception:
                print("Warning: WhatsApp buttons not found, leads may be empty.")

            print("Taking screenshot...")
            page.screenshot(path="dashboard_verification.png", full_page=True)
            print("Screenshot saved to dashboard_verification.png")

            # Click WhatsApp button if available (testing optimistic UI update)
            btn = page.locator('.btn-whatsapp').first
            if btn.is_visible():
                btn.click()
                time.sleep(1) # wait for animation/re-fetch
                page.screenshot(path="dashboard_verification_clicked.png", full_page=True)
                print("Clicked first lead, saved screenshot to dashboard_verification_clicked.png")

            browser.close()
    finally:
        server_process.kill()

if __name__ == '__main__':
    run_verification()
