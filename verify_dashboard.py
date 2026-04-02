from playwright.sync_api import sync_playwright
import urllib.request
import time
import subprocess
import os

def test_dashboard():
    # Start flask app
    env = os.environ.copy()
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    flask_process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for flask to start
    for _ in range(10):
        try:
            urllib.request.urlopen("http://localhost:5000/")
            break
        except Exception:
            time.sleep(1)

    # Generate some mock leads
    try:
        import db
        db.add_lead("Al-Shifa Clinic", "Clinic", "Bahawalpur", "03001234567")
        db.add_lead("Madina Store", "Store", "Bahawalpur", "03117654321")
        db.add_lead("Rizwan Services", "Service", "Bahawalpur", "03339876543")
    except Exception as e:
        print(f"Error adding leads: {e}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block external to prevent timeout in some envs
            page.route("**/*", lambda route: route.abort() if "googleapis" in route.request.url or "gstatic" in route.request.url else route.continue_())

            page.goto("http://localhost:5000/", wait_until='domcontentloaded')

            # Wait for table to populate
            page.wait_for_selector("#leads-body tr")

            rows = page.locator("#leads-body tr").count()
            print(f"Found {rows} leads in the table.")

            # Verify stats
            total = page.locator("#stat-total").inner_text()
            print(f"Total Stats: {total}")

            # Test WhatsApp button click
            btn = page.locator(".btn-whatsapp").first

            # Playwright handles new windows
            with page.expect_popup() as popup_info:
                btn.click()
            popup = popup_info.value

            # Allow some time for backend update
            time.sleep(1)

            print(f"Popup URL: {popup.url}")
            if "api.whatsapp.com" in popup.url or "whatsapp.com" in popup.url:
                print("WhatsApp redirection verified.")

            # Verify row is removed from UI
            new_rows = page.locator("#leads-body tr").count()
            print(f"Remaining rows in table: {new_rows}")

            # Verify stat update after some time
            page.evaluate("fetchStats()")
            time.sleep(1)
            new_contacted = page.locator("#stat-contacted").inner_text()
            print(f"Contacted Stats: {new_contacted}")

            page.screenshot(path="dashboard_verification.png")
            browser.close()
    finally:
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    test_dashboard()
