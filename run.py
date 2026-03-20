import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector
from db import init_db, get_db

app = Flask(__name__)

# Initialize DB on startup
init_db()

# Scheduler
scheduler = BackgroundScheduler()
is_collecting = False

def collect_leads_job():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler.add_job(func=collect_leads_job, trigger="interval", minutes=60, max_instances=1)
# Start the scheduler
scheduler.start()

# Shutdown scheduler on exit
import atexit
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads')
def get_leads():
    try:
        leads = collector.get_uncontacted_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        stats = collector.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "No ID provided"}), 400

    try:
        collector.mark_contacted(lead_id)
        # trigger collection
        global is_collecting
        if not is_collecting:
            scheduler.add_job(func=collect_leads_job, trigger='date') # run immediately
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Important: debug=False to avoid scheduler duplication
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port)
