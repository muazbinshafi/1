import os
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import collector

app = Flask(__name__)

# Global state for scraping
is_collecting = False
scheduler = BackgroundScheduler()
scheduler.start()

# Allowed static files for directory traversal safeguard
ALLOWED_FILES = ['style.css', 'app.js', 'index.html', 'dashboard.html']

def background_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads(getattr(collector, 'DB_PATH', 'leads.db'))
    finally:
        is_collecting = False

# Run collect_leads periodically, and immediately on startup
if scheduler.running:
    try:
        scheduler.add_job(func=background_collect, trigger="interval", minutes=60, next_run_time=datetime.now(), max_instances=1, id='collect_leads_job', replace_existing=True)
    except Exception as e:
        print(f"Failed to add job: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/leads')
def api_leads():
    try:
        with collector.get_db(getattr(collector, 'DB_PATH', 'leads.db')) as conn:
            leads = conn.execute("SELECT * FROM leads WHERE status = 'new'").fetchall()
            return jsonify([dict(lead) for lead in leads])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "No ID provided"}), 400

    try:
        with collector.get_db(getattr(collector, 'DB_PATH', 'leads.db')) as conn:
            conn.execute("UPDATE leads SET status = 'contacted' WHERE id = ?", (lead_id,))

        # Check remaining leads, and trigger scraping if low/empty
        with collector.get_db(getattr(collector, 'DB_PATH', 'leads.db')) as conn:
            remaining = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'").fetchone()[0]
            if remaining == 0 and not is_collecting:
                if scheduler.running:
                    try:
                        scheduler.add_job(func=background_collect, next_run_time=datetime.now(), max_instances=1, id='trigger_collect', replace_existing=True)
                    except Exception as e:
                        print(f"Failed to trigger job: {e}")

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<path:path>')
def send_static(path):
    if path in ALLOWED_FILES:
        return send_from_directory('.', path)
    if path.startswith('static/'):
        return send_from_directory('.', path)
    abort(404)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
