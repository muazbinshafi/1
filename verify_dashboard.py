from playwright.sync_api import sync_playwright
import time
import urllib.request
import os

def verify_dashboard():
    # Attempt to ping server
    try:
        urllib.request.urlopen('http://localhost:5000')
    except Exception as e:
        print(f"Error connecting to local server: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Route block to prevent external hangs if any
        page.route("**/*", lambda route: route.continue_() if "localhost" in route.request.url or "wa.me" in route.request.url or "whatsapp.com" in route.request.url else route.continue_())

        print("Navigating to dashboard...")
        page.goto('http://localhost:5000', wait_until='domcontentloaded')

        try:
            page.wait_for_selector('table tbody tr', timeout=10000)
            print("Dashboard loaded successfully.")
        except Exception:
            print("Table did not populate. Screenshotting state...")
            page.screenshot(path="dashboard_error.png")
            browser.close()
            return

        page.screenshot(path="dashboard_success.png")
        print("Took success screenshot.")

        # Optionally click first WA link
        print("Testing WhatsApp button click...")
        with page.expect_popup() as popup_info:
            page.locator('.btn-whatsapp').first.click()
        popup = popup_info.value
        time.sleep(2)
        popup.close()

        browser.close()
        print("Verification complete.")

if __name__ == '__main__':
    verify_dashboard()
