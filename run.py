from flask import Flask, render_template, jsonify, request
import collector
import threading
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

is_collecting = False
scheduler = BackgroundScheduler()

def background_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler.add_job(func=background_collection, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

def trigger_collection():
    threading.Thread(target=background_collection).start()

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
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        collector.mark_contacted(lead_id)
        # trigger collection
        trigger_collection()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No ID provided"}), 400

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
