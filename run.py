from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import database
import collector
import os

app = Flask(__name__)

# Global flag to prevent concurrent scraping jobs
is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        print("Collection already running, skipping...")
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

# Initialize the database and scheduler
database.init_db()

# Avoid starting scheduler twice if reloader is active
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    scheduler = BackgroundScheduler()
    # Run every 10 minutes in background
    scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=10, max_instances=1)
    scheduler.start()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = database.get_active_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = database.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def mark_contact():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        database.mark_lead_contacted(lead_id)
        return jsonify({"success": True, "message": "Lead marked as contacted"}), 200
    return jsonify({"success": False, "message": "Lead ID required"}), 400

if __name__ == '__main__':
    # Initial collection on startup
    if not is_collecting:
        import threading
        threading.Thread(target=scheduled_collection).start()

    # Run server with debug=False for security and scheduler stability
    app.run(debug=False, host='0.0.0.0', port=5000)
