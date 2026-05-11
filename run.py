import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import collector

app = Flask(__name__)
scheduler = BackgroundScheduler()
is_collecting = False

def background_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.scrape_leads()
    finally:
        is_collecting = False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    # Only return leads that haven't been contacted yet
    with collector.get_db() as conn:
        cur = conn.execute("SELECT * FROM leads WHERE contacted = 0")
        leads = [dict(row) for row in cur.fetchall()]
    return jsonify(leads)

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Lead ID required"}), 400

    with getattr(collector, 'DB_PATH_CONTEXT', collector).get_db() if hasattr(collector, 'DB_PATH_CONTEXT') else collector.get_db() as conn:
        conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger a new collection job when a lead is marked contacted
    if scheduler.running:
        try:
            scheduler.add_job(func=background_collect, id=f'scrape_job_manual_{datetime.now().timestamp()}', max_instances=1)
        except Exception as e:
            print(f"Failed to add manual job: {e}")

    return jsonify({"status": "success"})

@app.route('/<path:path>')
def static_proxy(path):
    # Allowlist to prevent directory traversal
    if path in ['style.css', 'app.js', 'index.html', 'dashboard.html']:
        return send_from_directory('.', path)
    if path.startswith('static/'):
        return send_from_directory('.', path)
    return "Not found", 404

if __name__ == '__main__':
    collector.setup_db()

    # Start background job if not running
    if not scheduler.running:
        scheduler.start()
        scheduler.add_job(func=background_collect, trigger="interval", hours=24, id='scrape_job', next_run_time=datetime.now(), max_instances=1, replace_existing=True)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
