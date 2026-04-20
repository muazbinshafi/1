import os
import subprocess
import time
import socket
import urllib.request
import sys

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    port = get_free_port()
    env = os.environ.copy()
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']
    env['PORT'] = str(port)

    print(f"Starting server on port {port}...")
    process = subprocess.Popen(['python3', 'run.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        time.sleep(3) # Give it time to start

        url = f"http://localhost:{port}/dashboard"
        print(f"Testing {url}...")

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            if "Universal Lead Collector" in html:
                print("Dashboard verification passed!")
                sys.exit(0)
            else:
                print("Dashboard title not found.")
                sys.exit(1)
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()