import subprocess
import time
import socket
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_verification():
    port = get_free_port()
    # Modify environment to run flask on free port without WERKZEUG conflicts
    import os
    env = os.environ.copy()
    env.pop('WERKZEUG_RUN_MAIN', None)

    # Pass custom port via env or modify run.py to use a port passed as env variable.
    # To keep things simple, we'll run it normally and assume port 5000 is open,
    # or pass PORT env var and read it in run.py
    env['PORT'] = str(port)
    flask_process = subprocess.Popen(
        ['python3', 'run.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    url = f"http://127.0.0.1:{port}"

    # Generate data
    subprocess.run(['python3', '-c', 'import collector; collector.generate_mock_leads()'])

    # Wait for server to be up using urllib (from memory guidelines)
    timeout = 10
    start = time.time()
    server_up = False
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{url}/dashboard")
            server_up = True
            break
        except urllib.error.URLError:
            time.sleep(0.5)

    if not server_up:
        flask_process.kill()
        raise Exception("Server failed to start")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Allow wa.me and whatsapp.com
            def route_handler(route):
                if 'wa.me' in route.request.url or 'whatsapp.com' in route.request.url:
                    route.continue_()
                elif '127.0.0.1' in route.request.url:
                    route.continue_()
                else:
                    route.abort()

            page.route("**/*", route_handler)
            page.goto(f"{url}/dashboard", wait_until='networkidle')

            print("Dashboard loaded.")

            # Verify analytics
            total_leads = page.locator('#total-leads').inner_text()
            print(f"Total leads displayed: {total_leads}")
            assert int(total_leads) >= 5

            # Click WhatsApp button
            with page.expect_popup() as popup_info:
                page.locator('.btn-whatsapp').first.click()

            popup = popup_info.value
            print(f"WhatsApp popup URL: {popup.url}")

            browser.close()
    finally:
        flask_process.terminate()
        flask_process.wait()

if __name__ == '__main__':
    run_verification()