import os
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__, static_folder='static')
scheduler = BackgroundScheduler()

is_collecting = False

def background_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads_job()
    finally:
        is_collecting = False

@app.route('/')
def serve_root():
    return send_from_directory('.', 'dashboard.html')

@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def serve_static_files(path):
    # Allowlist to prevent directory traversal
    allowed_files = ['style.css', 'app.js', 'index.html']
    if path in allowed_files:
        return send_from_directory('.', path)
    return send_from_directory('static', path)

@app.route('/api/leads', methods=['GET'])
def get_leads():
    with collector.get_db() as conn:
        rows = conn.execute("SELECT * FROM leads WHERE contacted = 0").fetchall()
        leads = [dict(row) for row in rows]
    return jsonify(leads)

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    with collector.get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0").fetchone()[0]
    return jsonify({
        'total': total,
        'contacted': contacted,
        'pending': pending
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID required'}), 400

    with collector.get_db() as conn:
        conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger new collection job if scheduler is running
    if scheduler.running:
        try:
            scheduler.add_job(background_collect, id=f'collect_{datetime.now().timestamp()}')
        except Exception as e:
            app.logger.error(f"Failed to add collection job: {e}")

    return jsonify({'success': True})

if __name__ == '__main__':
    collector.init_db()

    # Start scheduler for periodic collection (every 6 hours)
    if not scheduler.running:
        scheduler.add_job(background_collect, 'interval', hours=6, next_run_time=datetime.now(), max_instances=1)
        scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    # Allow background threads to finish properly on shutdown
    try:
        app.run(host='0.0.0.0', port=port, use_reloader=False)
    finally:
        if scheduler.running:
            scheduler.shutdown()
