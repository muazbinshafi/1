from flask import Flask, jsonify, request, send_from_directory, render_template, redirect
import os
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime
import collector

app = Flask(__name__)

# Scheduler configuration
scheduler = BackgroundScheduler()
is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

def initialize():
    collector.init_db()
    if not scheduler.running:
        scheduler.start()
        scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, id='lead_collection_job', replace_existing=True, next_run_time=datetime.now(), max_instances=1)

with app.app_context():
    initialize()

atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/stats')
def get_stats():
    with collector.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE contacted = 1")
        contacted = cursor.fetchone()['count']

        new_leads = total - contacted

        cursor.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
        leads = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads,
        'leads': leads
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')

    if lead_id:
        with collector.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

        try:
            if scheduler.running:
                scheduler.add_job(func=scheduled_collection, id=f'lead_collection_job_manual_{datetime.now().timestamp()}', replace_existing=True, max_instances=1)
        except Exception as e:
            print(f"Failed to schedule job: {e}")

        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Missing lead id'}), 400

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    collector.init_db()
    if not scheduler.running:
        scheduler.start()
        scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, id='lead_collection_job', replace_existing=True, next_run_time=datetime.now(), max_instances=1)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
