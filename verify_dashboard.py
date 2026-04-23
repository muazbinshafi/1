import urllib.request
import subprocess
import time
import socket
import json
import os

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def verify_dashboard():
    port = get_free_port()
    env = os.environ.copy()
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']
    env['PORT'] = str(port)

    print(f"Starting Flask server on port {port} for dashboard verification...")
    process = subprocess.Popen(['python3', 'run.py'], env=env)

    try:
        # Wait for server to start
        time.sleep(2)

        # Test dashboard html
        req = urllib.request.Request(f'http://127.0.0.1:{port}/')
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')

        assert 'Universal Lead Collector' in html
        assert 'Bahawalpur' in html
        print("Dashboard HTML loads correctly!")

        # Test static js
        req = urllib.request.Request(f'http://127.0.0.1:{port}/static/js/script.js')
        response = urllib.request.urlopen(req)
        js = response.read().decode('utf-8')

        assert 'sendWhatsApp' in js
        assert 'generateMessage' in js
        print("Static JS loads correctly!")

        # Test API
        req = urllib.request.Request(f'http://127.0.0.1:{port}/api/leads')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))

        assert 'leads' in data
        assert 'stats' in data
        print("API endpoint /api/leads works correctly!")

    finally:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    verify_dashboard()
