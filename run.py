from flask import Flask, render_template, jsonify, request
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

# Global flag to prevent concurrent collections
is_collecting = False

@app.before_request
def initialize():
    collector.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    leads = collector.get_uncontacted_leads()
    return jsonify([dict(lead) for lead in leads])

@app.route('/api/stats', methods=['GET'])
def api_stats():
    stats = collector.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        collector.mark_contacted(lead_id)
        # Trigger background collection asynchronously
        trigger_collection()
        return jsonify({"success": True}), 200
    return jsonify({"error": "Invalid lead id"}), 400

@app.route('/api/collect', methods=['POST'])
def api_collect():
    trigger_collection()
    return jsonify({"success": True, "message": "Collection triggered"}), 200

def trigger_collection():
    global is_collecting
    if not is_collecting:
        is_collecting = True
        thread = threading.Thread(target=run_collection)
        thread.start()

def run_collection():
    global is_collecting
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

if __name__ == '__main__':
    # Initialize DB
    collector.init_db()

    # Trigger an initial collection on startup
    trigger_collection()

    # Setup APScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=trigger_collection, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    # Disable debug mode to prevent dual execution of scheduler in production-like contexts
    app.run(host='0.0.0.0', port=5000, debug=False)
