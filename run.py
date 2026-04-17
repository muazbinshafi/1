from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime
import collector
import sqlite3

app = Flask(__name__)
scheduler = BackgroundScheduler()
is_collecting = False

@app.route('/')
def serve_index():
    return send_from_directory('static', 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    if path in ['index.html', 'style.css', 'app.js']:
        return send_from_directory('.', path)
    return send_from_directory('static', path)

@app.route('/api/leads')
def get_leads():
    try:
        with collector.get_db() as conn:
            leads = conn.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC").fetchall()
            return jsonify([dict(lead) for lead in leads])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    try:
        with collector.get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
            return jsonify({"total": total, "contacted": contacted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Lead ID required"}), 400

    try:
        with collector.get_db() as conn:
            conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

        # Trigger background collection if not already running
        if scheduler.running:
            try:
                scheduler.add_job(func=run_collection, trigger='date', run_date=datetime.now(), id=f'scrape_job_manual_{datetime.now().timestamp()}')
            except Exception as e:
                print(f"Failed to add job: {e}")

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

if __name__ == '__main__':
    collector.init_db()

    # Check if this is the main process before starting scheduler to avoid duplicate jobs in debug mode
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler.add_job(func=run_collection, trigger="interval", hours=24, id='scrape_job', replace_existing=True, next_run_time=datetime.now(), max_instances=1)
        scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
