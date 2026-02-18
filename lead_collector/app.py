from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os
import sys

# Ensure we can import from lead_collector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lead_collector import models
from lead_collector.scrapers import MockScraper

app = Flask(__name__)

# Initialize DB
models.init_db()

def collect_leads():
    print("Starting lead collection...")
    scraper = MockScraper(count=5)
    leads = scraper.fetch_leads()
    count = 0
    for lead in leads:
        # We assume add_lead returns True if added, False if duplicate
        if models.add_lead(lead['name'], lead['type'], lead['city'], lead['phone']):
            count += 1
    print(f"Collected {count} new leads.")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=collect_leads, trigger="interval", minutes=60)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = models.get_leads(status='new')
    return jsonify(leads)

@app.route('/api/leads/<int:lead_id>/contact', methods=['POST'])
def contact_lead(lead_id):
    models.update_lead_status(lead_id, 'contacted')
    return jsonify({'success': True})

@app.route('/api/trigger_collection', methods=['POST'])
def trigger_collection():
    collect_leads()
    return jsonify({'success': True})

if __name__ == '__main__':
    # Pre-populate some leads on startup if empty
    if not models.get_leads():
        collect_leads()
    app.run(debug=True, host='0.0.0.0', port=5000)
