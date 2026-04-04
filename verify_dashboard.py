import urllib.request
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

def verify_dashboard():
    port = get_free_port()

    # Start the Flask app
    env = {"PYTHONPATH": "/app", "PORT": str(port)}
    # Remove WERKZEUG_RUN_MAIN to prevent KeyErrors
    import os
    env.update(os.environ.copy())
    if "WERKZEUG_RUN_MAIN" in env:
        del env["WERKZEUG_RUN_MAIN"]

    flask_process = subprocess.Popen(
        ['python3', 'run.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for the server to start
        url = f"http://localhost:{port}"
        time.sleep(2)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Seed the database before testing
            import collector
            import run
            # Ensure DB is initialized
            run.init_db()
            leads = collector.generate_mock_leads()
            with run.get_db() as conn:
                for lead in leads:
                    try:
                        conn.execute('''
                            INSERT INTO leads (business_name, type, city, phone)
                            VALUES (?, ?, ?, ?)
                        ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
                    except:
                        pass

            page.goto(url, wait_until="networkidle", timeout=10000)

            # Wait for data to load
            try:
                page.wait_for_selector("#leads-body tr td", timeout=5000)
            except Exception:
                pass

            # Take screenshot
            page.screenshot(path="dashboard_verification.png", full_page=True)
            print("Dashboard screenshot saved to dashboard_verification.png")

            # Verify UI elements
            assert page.locator("h1:has-text('Universal Lead Collector')").is_visible()
            assert page.locator(".stat-card").count() == 3
            assert page.locator("#leads-body tr").count() > 0

            print("Verification successful!")
            browser.close()

    finally:
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    verify_dashboard()
