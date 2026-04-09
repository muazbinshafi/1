import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector
from datetime import datetime

app = Flask(__name__)

# Track if currently collecting to prevent overlap
is_collecting = False

def background_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
# Run background_collection right away, and then every 6 hours
scheduler.add_job(func=background_collection, trigger="interval", hours=6, next_run_time=datetime.now(), max_instances=1)
# Only start scheduler if we are not in debug mode or if it's the main process in debug mode
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler.start()

@app.route('/')
def index():
    # If this is the dashboard, return the dashboard template
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    # Allow testing to override DB path by patching collector.DB_PATH
    with collector.get_db() as conn:
        cursor = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    with collector.get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
    return jsonify({'total': total, 'contacted': contacted, 'new': new})

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID required'}), 400

    with collector.get_db() as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger a new collection in the background if possible
    if scheduler.running:
        scheduler.add_job(func=background_collection, next_run_time=datetime.now())

    return jsonify({'success': True})

if __name__ == '__main__':
    # Initialize DB
    collector.init_db()

    # Run Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
