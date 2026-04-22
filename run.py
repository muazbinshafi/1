import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
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
        collector.collect_leads()
    finally:
        is_collecting = False

@app.before_request
def init_db():
    collector.setup_db()

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    with collector.get_db() as conn:
        cursor = conn.execute("SELECT * FROM leads WHERE is_contacted = 0 ORDER BY created_at DESC")
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Lead ID required"}), 400

    with collector.get_db() as conn:
        conn.execute("UPDATE leads SET is_contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger a background collection if scheduler is running
    if scheduler.running:
        try:
            scheduler.add_job(func=background_collect, trigger='date', next_run_time=datetime.now(), max_instances=1)
        except Exception:
            pass

    return jsonify({"success": True})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    with collector.get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE is_contacted = 1").fetchone()[0]
    return jsonify({
        "total_leads": total,
        "contacted_leads": contacted
    })

@app.route('/<path:path>')
def catch_all(path):
    allowed_files = ['style.css', 'app.js', 'index.html', 'dashboard.html']
    if path in allowed_files:
        return send_from_directory('.', path)
    if path.startswith('static/'):
        return send_from_directory('.', path)
    return "Not Found", 404

if __name__ == '__main__':
    # Initialize DB and run first scrape
    collector.setup_db()

    # Setup scheduler for periodic scrape (e.g., every 2 hours)
    scheduler.add_job(func=background_collect, trigger='interval', hours=2, id='periodic_scrape', max_instances=1)
    # Also trigger an immediate scrape
    scheduler.add_job(func=background_collect, trigger='date', next_run_time=datetime.now(), id='startup_scrape', max_instances=1)
    scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    finally:
        if scheduler.running:
            scheduler.shutdown()
