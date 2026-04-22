import urllib.request
import urllib.error
import subprocess
import time
import socket
import os

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def verify_dashboard():
    port = find_free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']

    print(f"Starting Flask server on port {port}...")
    process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for startup

    success = False
    try:
        url = f"http://localhost:{port}/dashboard"
        print(f"Fetching {url}")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            if "Universal Lead Collector" in html and "leads-table" in html:
                print("✅ Dashboard HTML loaded successfully.")
                success = True
            else:
                print("❌ Dashboard HTML missing expected content.")

        # Test API
        api_url = f"http://localhost:{port}/api/leads"
        print(f"Fetching {api_url}")
        api_req = urllib.request.Request(api_url)
        with urllib.request.urlopen(api_req) as api_response:
            data = api_response.read().decode('utf-8')
            if "[" in data and "]" in data:
                print("✅ API returns JSON array.")
            else:
                print("❌ API failed to return JSON array.")
                success = False

    except urllib.error.URLError as e:
        print(f"❌ Connection failed: {e}")
    finally:
        process.terminate()
        process.wait()

    if not success:
        exit(1)

if __name__ == '__main__':
    verify_dashboard()
