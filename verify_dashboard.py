import subprocess
import time
import socket
import urllib.request
import os
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    port = get_free_port()

    env = os.environ.copy()
    env['PORT'] = str(port)
    env['PYTHONPATH'] = os.path.abspath('.')
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    print("Generating mock leads for test...")
    subprocess.run(['python', '-c', 'import collector; collector.init_db(); collector.generate_mock_leads()'], env=env)

    print(f"Starting server on port {port}...")
    server = subprocess.Popen(['python', 'run.py'], env=env)

    # Wait for server
    max_retries = 30
    for i in range(max_retries):
        try:
            urllib.request.urlopen(f'http://localhost:{port}')
            print("Server is up!")
            break
        except Exception:
            time.sleep(1)
    else:
        server.kill()
        raise Exception("Server failed to start")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def handle_route(route):
                url = route.request.url
                if 'localhost' in url or 'whatsapp.com' in url or 'wa.me' in url:
                    route.continue_()
                else:
                    route.abort()

            page.route("**/*", handle_route)

            print("Navigating to dashboard...")
            page.goto(f'http://localhost:{port}', wait_until='domcontentloaded')
            page.wait_for_selector('#leads-body tr')

            print("Taking dashboard screenshot...")
            page.screenshot(path='dashboard.png')

            # Click send whatsapp
            with page.expect_popup() as popup_info:
                page.click('.btn-whatsapp')
            popup = popup_info.value

            print("Popup opened, checking url...")
            try:
                popup.wait_for_load_state(timeout=5000)
            except Exception:
                pass # it's fine if it times out loading wa.me

            print(f"Popup url: {popup.url}")
            assert 'wa.me' in popup.url or 'whatsapp.com' in popup.url
            print("WhatsApp link verification passed.")

            browser.close()
    finally:
        server.kill()

if __name__ == '__main__':
    main()
