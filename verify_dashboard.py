import os
import sys
import time
import subprocess
import socket
import urllib.request
from playwright.sync_api import sync_playwright

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def wait_for_server(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f'http://localhost:{port}/api/stats', timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False

def verify_dashboard():
    port = get_free_port()

    # Run the flask app as a subprocess
    env = os.environ.copy()
    env.pop('WERKZEUG_RUN_MAIN', None) # Prevent double start

    # We'll dynamically patch run.py to run on the chosen port if we pass it as env, or just modify code to read env
    # For simplicity, let's inject it via a small wrapper
    wrapper_script = f"""
import run
run.init_db()
import collector
collector.generate_mock_leads() # Ensure data
run.app.run(port={port}, debug=False)
"""
    with open('start_test_server.py', 'w') as f:
        f.write(wrapper_script)

    process = subprocess.Popen([sys.executable, 'start_test_server.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        if not wait_for_server(port):
            print("Failed to start server")
            return False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            print(f"Connecting to http://localhost:{port}/")
            page.goto(f'http://localhost:{port}/')

            # Wait for table to populate (since we called generate_mock_leads, there should be some)
            try:
                page.wait_for_selector('.btn-whatsapp', timeout=5000)
                print("Leads populated successfully.")
            except Exception as e:
                print("Leads failed to populate within timeout.")
                return False

            # Take screenshot of the dashboard
            page.screenshot(path="dashboard_verification.png")
            print("Screenshot saved to dashboard_verification.png")

            # Test WhatsApp logic
            # Listen for new pages (window.open)
            with context.expect_page() as new_page_info:
                page.locator('.btn-whatsapp').first.click()

            new_page = new_page_info.value
            try:
                new_page.wait_for_load_state('domcontentloaded')
            except:
                pass # Ignored timeout if the load state is not reached completely but url is accessible

            # Check if URL matches WhatsApp structure
            wa_url = new_page.url
            if 'api.whatsapp.com' in wa_url or 'whatsapp.com' in wa_url:
                print("WhatsApp URL verification successful:", wa_url)
                return True
            else:
                print("WhatsApp URL verification failed. Got:", wa_url)
                return False

    finally:
        process.terminate()
        process.wait()
        if os.path.exists('start_test_server.py'):
            os.remove('start_test_server.py')

if __name__ == '__main__':
    success = verify_dashboard()
    if not success:
        sys.exit(1)
    print("Verification completed successfully.")
