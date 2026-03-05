import time
import urllib.request
import json

def test_dashboard():
    # Wait for the server to start
    time.sleep(2)

    # Check dashboard page
    req = urllib.request.Request('http://127.0.0.1:5000/')
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        html = response.read().decode()
        assert 'Universal Lead Collector' in html

    # Check leads API
    req = urllib.request.Request('http://127.0.0.1:5000/api/leads')
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        leads = json.loads(response.read().decode())
        assert isinstance(leads, list)

    # Check stats API
    req = urllib.request.Request('http://127.0.0.1:5000/api/stats')
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        stats = json.loads(response.read().decode())
        assert 'total' in stats
        assert 'new' in stats
        assert 'contacted' in stats

    print("Dashboard APIs verified successfully!")

if __name__ == '__main__':
    test_dashboard()
