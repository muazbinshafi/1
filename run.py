from flask import Flask, render_template, jsonify, request
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

# Ensure db is initialized
collector.init_db()

is_collecting = False

def scheduled_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collect, trigger="interval", hours=1, max_instances=1)
scheduler.start()

# Run once at startup
threading.Thread(target=scheduled_collect).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    try:
        leads = collector.get_uncontacted_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = collector.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/collect', methods=['POST'])
def trigger_collect():
    try:
        threading.Thread(target=scheduled_collect).start()
        return jsonify({"success": True, "message": "Collection started"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    try:
        data = request.get_json()
        lead_id = data.get('id')
        if lead_id:
            collector.mark_contacted(lead_id)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Missing lead id"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
