import os
import threading
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

is_collecting = False
collect_lock = threading.Lock()

def collect_leads_job():
    global is_collecting
    with collect_lock:
        if is_collecting:
            return
        is_collecting = True

    try:
        collector.collect_new_leads()
    finally:
        with collect_lock:
            is_collecting = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = collector.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = collector.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    collector.mark_lead_contacted(lead_id)

    # Trigger a background collection job when a lead is contacted
    threading.Thread(target=collect_leads_job).start()

    return jsonify({'success': True, 'message': 'Lead marked as contacted'})

if __name__ == '__main__':
    # Scheduler logic
    scheduler = BackgroundScheduler()
    # Run every 6 hours by default
    scheduler.add_job(func=collect_leads_job, trigger="interval", hours=6, max_instances=1)
    scheduler.start()

    # Also run immediately on startup if we have no uncontacted leads
    if len(collector.get_uncontacted_leads()) == 0:
        threading.Thread(target=collect_leads_job).start()

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
