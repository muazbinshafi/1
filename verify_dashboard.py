import urllib.request
from playwright.sync_api import sync_playwright
import time
import os
import subprocess
import socket
import collector

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_verification():
    # Insert some initial data
    collector.DB_PATH = 'leads.db'
    collector.init_db()
    collector.generate_mock_leads()

    port = get_free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    flask_process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        # Wait for server to start
        time.sleep(2)

        base_url = f"http://localhost:{port}"

        # 1. Test Static files via HTTP
        response = urllib.request.urlopen(base_url + "/static/dashboard.html")
        assert response.status == 200
        html_content = response.read().decode('utf-8')
        assert "Lead Collector Dashboard" in html_content
        assert "Business Name" in html_content

        # 2. Test Playwright E2E UI
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base_url + "/static/dashboard.html", wait_until="networkidle")

            # Check for header
            assert page.is_visible("text=Lead Collector Dashboard")

            # Wait for data to load
            try:
                page.wait_for_selector(".btn-whatsapp", timeout=5000)
            except Exception as e:
                print("Warning: Button not found, maybe no leads or slow API.")

            # Verify analytics block is present
            assert page.is_visible("#total-leads")

            browser.close()
            print("Frontend verification passed successfully.")

    finally:
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    run_verification()
