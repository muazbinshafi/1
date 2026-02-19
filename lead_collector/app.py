import sys
import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

# Ensure the root directory is in sys.path if running as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lead_collector.models import init_db, Lead
from lead_collector.collector import collect_leads

app = Flask(__name__)

# Scheduler Setup
scheduler = BackgroundScheduler()
# Run collect_leads every 24 hours
scheduler.add_job(func=collect_leads, trigger="interval", hours=24)
scheduler.start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = Lead.get_leads(status='new')
    return jsonify(leads)

@app.route('/api/collect', methods=['POST'])
def manual_collect():
    count = collect_leads()
    return jsonify({"success": True, "count": count})

@app.route('/api/contact/<int:lead_id>', methods=['POST'])
def contact_lead(lead_id):
    Lead.update_status(lead_id, 'contacted')
    return jsonify({"success": True})

@app.route('/api/analytics', methods=['GET'])
def analytics():
    data = Lead.get_analytics()
    return jsonify(data)

if __name__ == '__main__':
    # Initialize DB on start
    init_db()
    # Seed initial data if DB is empty (optional check, or just run collection once)
    # For demo purposes, let's collect some if empty
    leads = Lead.get_leads()
    if not leads:
        print("No leads found, collecting initial batch...")
        collect_leads()

    app.run(debug=True, host='0.0.0.0', port=5000)
