import socket
import subprocess
import time
import os
import urllib.request
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_verification():
    port = get_free_port()
    print(f"Starting server on port {port}...")

    env = os.environ.copy()
    env['PORT'] = str(port)
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    url = f"http://localhost:{port}"
    max_retries = 30
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            print("Server is up!")
            break
        except Exception:
            time.sleep(1)
            if i == max_retries - 1:
                print("Server failed to start")
                process.terminate()
                return

    # Seed some mock data so the dashboard isn't empty
    print("Generating mock leads for visual verification...")
    subprocess.run(['python3', '-c', 'import collector; collector.generate_mock_leads()'])

    print("Running Playwright verification...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external to prevent timeouts on wa.me redirects if clicked
            page.route("**/*", lambda route: route.continue_() if "localhost" in route.request.url or "wa.me" in route.request.url or "whatsapp.com" in route.request.url else route.abort())

            page.goto(url)
            page.wait_for_selector('table', timeout=5000)

            # Take screenshot of dashboard
            page.screenshot(path="dashboard_screenshot.png")
            print("Dashboard screenshot saved to dashboard_screenshot.png")

            browser.close()
    except Exception as e:
        print(f"Verification error: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    run_verification()
