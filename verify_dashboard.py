import urllib.request
import os
import time
import socket
import threading
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
import run
import collector

def verify_dashboard():
    # Setup test DB
    db_path = 'test_verify_leads.db'
    collector.DB_PATH = db_path
    if os.path.exists(db_path):
        os.remove(db_path)

    collector.init_db()
    collector.generate_mock_leads()

    # Find available port
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    # Start Flask app
    server = make_server('127.0.0.1', port, run.app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    try:
        # Check backend responds with urllib.request as per memory instructions
        req = urllib.request.Request(f'http://127.0.0.1:{port}/api/stats')
        response = urllib.request.urlopen(req)
        assert response.status == 200

        # Take visual screenshot
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f'http://127.0.0.1:{port}')
            page.wait_for_selector('table.leads-table tbody tr')
            page.screenshot(path='dashboard_verification.png')
            print(f"Verification screenshot saved to dashboard_verification.png on port {port}")
            browser.close()

    finally:
        server.shutdown()
        thread.join()

        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == '__main__':
    verify_dashboard()
