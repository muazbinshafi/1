import subprocess
import time
import urllib.request
import os

env = os.environ.copy()
if 'WERKZEUG_RUN_MAIN' in env:
    del env['WERKZEUG_RUN_MAIN']
env['PORT'] = '5001'

p = subprocess.Popen(['python3', 'run.py'], env=env)
time.sleep(2)
try:
    req = urllib.request.Request('http://127.0.0.1:5001/api/analytics')
    response = urllib.request.urlopen(req)
    print("Analytics Status:", response.status)
finally:
    p.terminate()
