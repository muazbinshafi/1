from playwright.sync_api import sync_playwright
import time
import subprocess
import os

def main():
    # Setup mock DB first
    os.system('python -c "from database import init_db; init_db()"')
    os.system('python -c "import collector; from database import get_db; leads = collector.generate_mock_leads(); \nwith get_db() as conn:\n  cursor = conn.cursor()\n  for l in leads:\n    cursor.execute(\\"INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)\\", (l[\'business_name\'], l[\'type\'], l[\'city\'], l[\'phone\']))"')

    # Start flask app
    flask_env = os.environ.copy()
    flask_env.pop('WERKZEUG_RUN_MAIN', None)

    server = subprocess.Popen(['python3', 'run.py'], env=flask_env)
    time.sleep(3) # Wait for startup

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to dashboard
            page.goto("http://localhost:5000", wait_until='networkidle')

            # Wait for JS to populate tables via API
            try:
                page.wait_for_selector('table tbody tr', timeout=5000)
            except:
                print("Warning: Table might not be populated or timed out.")

            # Save screenshot
            page.screenshot(path="verification.png", full_page=True)
            print("Saved verification screenshot to verification.png")
            browser.close()
    finally:
        server.terminate()
        server.wait()

if __name__ == '__main__':
    main()
