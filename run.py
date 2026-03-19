import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
is_collecting = False

def scheduled_collection():
    global is_collecting
    if not is_collecting:
        is_collecting = True
        try:
            print("Running scheduled lead collection...")
            collector.collect_leads()
        finally:
            is_collecting = False

@app.before_request
def initialize():
    if not hasattr(app, 'initialized'):
        collector.init_db()
        app.initialized = True

        # Start the background scheduler
        scheduler = BackgroundScheduler()
        # Initial run on startup if debugging is off, otherwise duplicate jobs can occur
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # Run initial collection
            scheduled_collection()
            # Schedule periodic run every hour
            scheduler.add_job(func=scheduled_collection, trigger="interval", hours=1, max_instances=1)
            scheduler.start()

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
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        collector.mark_contacted(lead_id)

        # Trigger background collection if we marked someone, helps keep pipeline full
        from threading import Thread
        Thread(target=scheduled_collection).start()

        return jsonify({"success": True, "message": "Lead marked as contacted."})
    return jsonify({"success": False, "message": "No lead ID provided."}), 400

if __name__ == '__main__':
    collector.init_db()
    # Debug=False is recommended to avoid duplicate scheduler runs
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port)
