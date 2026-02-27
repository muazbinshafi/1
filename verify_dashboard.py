from playwright.sync_api import sync_playwright
import time

def verify_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the dashboard
        print("Navigating to dashboard...")
        page.goto("http://localhost:5000")

        # Wait for the table to load
        page.wait_for_selector("table#leads-table", timeout=10000)

        # Wait a bit for the async fetch to populate rows
        time.sleep(2)

        # Take a screenshot
        screenshot_path = "/home/jules/verification/dashboard_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_dashboard()
