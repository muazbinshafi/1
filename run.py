import os
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

# Scheduler setup
scheduler = BackgroundScheduler()
is_collecting = False
collect_lock = threading.Lock()

def background_collect():
    global is_collecting
    with collect_lock:
        if is_collecting:
            return
        is_collecting = True

    try:
        collector.scrape_leads()
    finally:
        with collect_lock:
            is_collecting = False

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    allowed_files = ['style.css', 'index.html', 'dashboard.html']
    if path in allowed_files:
        return send_from_directory('.', path)
    if path.startswith('static/'):
        # Allow files in static dir
        return send_from_directory('.', path)
    return "Not Found", 404

@app.route('/api/leads')
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as db:
        cursor = db.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC")
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as db:
        total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = db.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
        active = db.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0").fetchone()[0]
    return jsonify({"total": total, "contacted": contacted, "active": active})

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Missing ID"}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as db:
        db.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger background collection
    if scheduler.running:
        try:
            scheduler.add_job(func=background_collect, trigger="date", run_date=datetime.now(), id=f"collect_after_contact_{lead_id}", replace_existing=True)
        except Exception as e:
            print(f"Failed to add job: {e}")

    return jsonify({"success": True})

if __name__ == '__main__':
    # Initialize DB and start initial collection
    collector.init_db()

    # Configure scheduler
    scheduler.add_job(func=background_collect, trigger="interval", hours=24, id="daily_collection", replace_existing=True)
    if scheduler.running is False:
        scheduler.start()

    # Trigger initial scrape on startup
    scheduler.add_job(func=background_collect, trigger="date", run_date=datetime.now(), id="startup_collection", replace_existing=True)

    port = int(os.environ.get('PORT', 5000))
    # Workaround for testing, avoiding port conflicts
    env = os.environ.copy()
    if 'WERKZEUG_RUN_MAIN' in env:
        del env['WERKZEUG_RUN_MAIN']
    app.run(host='0.0.0.0', port=port, debug=True)