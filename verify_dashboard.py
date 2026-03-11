import time
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

def verify():
    # Wait for server to start
    max_retries = 30
    for i in range(max_retries):
        try:
            urllib.request.urlopen("http://localhost:5000", timeout=1)
            print("Server is up!")
            break
        except urllib.error.URLError:
            time.sleep(1)
            print(f"Waiting for server... ({i+1}/{max_retries})")
    else:
        print("Server did not start in time.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Block external fonts to avoid hanging in network restricted environments
        page.route("**/*.{ttf,woff,woff2,eot,svg}", lambda route: route.abort())
        page.route("**/fonts.googleapis.com/**", lambda route: route.abort())

        page.goto("http://localhost:5000")

        # Wait for data to load
        try:
            page.wait_for_selector(".btn-whatsapp", timeout=10000)
        except Exception:
            # Let's check what's on the page if it fails
            page.screenshot(path="dashboard_screenshot_error.png")
            print("Failed to find WhatsApp button. Screenshot saved to dashboard_screenshot_error.png")
            print("Page HTML:")
            print(page.content())
            return

        # Take a screenshot
        page.screenshot(path="dashboard_screenshot.png")
        print("Dashboard loaded successfully and screenshot taken.")

        # Verify stats are populated
        total = page.locator("#stat-total").inner_text()
        print(f"Total leads reported: {total}")

        browser.close()

if __name__ == "__main__":
    verify()
