from playwright.sync_api import sync_playwright
import os
import shutil

# Make sure we use a test db with some data for the UI
import sqlite3
import run
import collector

def setup_test_db():
    db_path = 'leads.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    collector.DB_PATH = db_path
    collector.generate_mock_leads(db_path)

def run_cuj(page):
    page.goto("http://localhost:5000", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Initial state
    page.screenshot(path="/home/jules/verification/screenshots/dashboard_initial.png")
    page.wait_for_timeout(500)

    # Click the first 'Send WhatsApp' button
    btn = page.locator('.btn-whatsapp').first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(1000)

    # Verify optimistic update
    page.screenshot(path="/home/jules/verification/screenshots/dashboard_after_click.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    setup_test_db()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
