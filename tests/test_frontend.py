from playwright.sync_api import sync_playwright
import time

def test_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the dashboard
        print("Navigating to dashboard...")
        page.goto("http://localhost:5000")

        # Verify title
        assert "Universal Lead Collector" in page.title()
        print("Title verified.")

        # Wait for table to load
        page.wait_for_selector("table#leads-table", timeout=10000)
        print("Table found.")

        # Check if leads are present (wait a bit for async fetch)
        time.sleep(2)
        rows = page.locator("tbody tr").count()
        print(f"Found {rows} rows in the table.")

        # We expect at least one row from our earlier run or initial seeding
        if rows > 0:
            # Check for button
            btn = page.locator("tbody tr:first-child .whatsapp-btn")
            assert btn.is_visible()
            print("WhatsApp button visible.")
        else:
            print("No leads displayed - check backend or database state.")

        browser.close()

if __name__ == "__main__":
    test_frontend()
