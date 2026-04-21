import urllib.request
import subprocess
import time
import os

env = os.environ.copy()
if 'WERKZEUG_RUN_MAIN' in env:
    del env['WERKZEUG_RUN_MAIN']
env['PORT'] = '5002'

print("Starting Flask server for verification...")
p = subprocess.Popen(['python3', 'run.py'], env=env)
time.sleep(2)

try:
    print("Fetching dashboard.html...")
    req = urllib.request.Request('http://127.0.0.1:5002/')
    res = urllib.request.urlopen(req)
    html = res.read().decode('utf-8')
    assert 'Universal Lead Collector' in html
    assert '<table class="leads-table">' in html

    print("Fetching style.css...")
    req_css = urllib.request.Request('http://127.0.0.1:5002/static/css/style.css')
    res_css = urllib.request.urlopen(req_css)
    css = res_css.read().decode('utf-8')
    assert 'var(--primary-dark)' in css

    print("Fetching script.js...")
    req_js = urllib.request.Request('http://127.0.0.1:5002/static/js/script.js')
    res_js = urllib.request.urlopen(req_js)
    js = res_js.read().decode('utf-8')
    assert 'fetchAnalytics()' in js

    print("Dashboard verification passed.")
finally:
    p.terminate()
