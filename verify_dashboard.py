import urllib.request
import time
from playwright.sync_api import sync_playwright

def verify_dashboard():
    # Wait for server to boot
    for _ in range(30):
        try:
            urllib.request.urlopen("http://localhost:5000", timeout=1)
            break
        except:
            time.sleep(1)
    else:
        print("Server didn't start in time.")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate
            page.goto('http://localhost:5000')

            # Wait for content to load
            page.wait_for_selector('table')

            # Take screenshot to verify UI manually later if needed
            page.screenshot(path="dashboard_screenshot.png")

            # Check title
            assert "Universal Lead Collector" in page.title()

            # Check headers
            headers = page.locator('th').all_inner_texts()
            assert "Business Name" in headers
            assert "Action" in headers

            # Wait for JS to populate data
            page.wait_for_timeout(2000)

            print("UI Verification Passed.")
            browser.close()
            return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"UI Verification Failed: {e}")
        return False

if __name__ == "__main__":
    verify_dashboard()
