import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from db import init_db, get_db
from collector import collect_leads

app = Flask(__name__)

is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
# Run daily at midnight and also immediately on startup
scheduler.add_job(func=scheduled_collection, trigger="interval", days=1, next_run_time=datetime.now(), max_instances=1)
scheduler.start()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_uncontacted_leads():
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
        leads = [dict(row) for row in cur.fetchall()]
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0").fetchone()[0]
    return jsonify({"total": total, "contacted": contacted, "new": new})

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Missing ID"}), 400

    with get_db() as conn:
        conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger new background collection if a lead is contacted
    global is_collecting
    if not is_collecting:
        # Schedule it a few seconds later to avoid blocking the request
        scheduler.add_job(func=scheduled_collection, next_run_time=datetime.now(), max_instances=1)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    init_db()

    # Remove WERKZEUG_RUN_MAIN to prevent duplicate scheduler execution in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        pass

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
