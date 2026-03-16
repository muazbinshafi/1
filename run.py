from flask import Flask, render_template, jsonify, request
import database
import collector
from apscheduler.schedulers.background import BackgroundScheduler
import threading

app = Flask(__name__)

# Global flag to prevent concurrent collections
is_collecting = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = database.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = database.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    if not data or 'lead_id' not in data:
        return jsonify({'error': 'Missing lead_id'}), 400

    lead_id = data['lead_id']
    try:
        database.mark_contacted(lead_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

if __name__ == '__main__':
    database.init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    try:
        # Initial run on startup in a separate thread
        threading.Thread(target=scheduled_collection).start()

        # Disable debug mode in production-like contexts to prevent double scheduling
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        scheduler.shutdown()
