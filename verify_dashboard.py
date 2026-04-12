import sys
from playwright.sync_api import sync_playwright
import urllib.request
import time
import socket

def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url)
            return True
        except Exception:
            time.sleep(1)
    return False

def verify_dashboard():
    port = sys.argv[1] if len(sys.argv) > 1 else "5000"
    url = f"http://127.0.0.1:{port}"

    if not wait_for_server(url):
        print("Server did not start in time.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("Navigating to dashboard...")
            page.goto(url, wait_until="domcontentloaded")

            # Wait for leads table to populate (backend might be slow collecting initial leads)
            print("Waiting for leads to load...")
            try:
                page.wait_for_selector(".btn-whatsapp", timeout=15000)
            except Exception as e:
                print("Warning: Leads table took too long to load or is empty. Proceeding anyway.", e)

            # verify elements
            title = page.locator("h1").inner_text()
            assert "Universal Lead Collector Dashboard" in title, f"Unexpected title: {title}"

            # Take screenshot
            page.screenshot(path="dashboard_verification.png", full_page=True)
            print("Dashboard verified and screenshot saved.")

        except AssertionError as e:
            print(f"Assertion Error: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    verify_dashboard()
