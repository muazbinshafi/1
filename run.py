from flask import Flask, jsonify, request, send_from_directory, render_template, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import os
import collector
import sqlite3

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

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    allowed_files = ['style.css', 'app.js', 'index.html', 'dashboard.html', 'static/css/dashboard.css', 'static/js/script.js']
    if path in allowed_files:
        return send_from_directory('.', path)
    return "Not Found", 404

@app.route('/api/leads', methods=['GET'])
def get_leads():
    try:
        with collector.get_db() as db:
            cursor = db.execute("SELECT * FROM leads WHERE status='pending'")
            pending_leads = [dict(row) for row in cursor.fetchall()]

            cursor = db.execute("SELECT COUNT(*) as count FROM leads WHERE status='contacted'")
            contacted_count = cursor.fetchone()['count']

            cursor = db.execute("SELECT COUNT(*) as count FROM leads")
            total_count = cursor.fetchone()['count']

        return jsonify({
            'leads': pending_leads,
            'stats': {
                'total': total_count,
                'contacted': contacted_count,
                'pending': len(pending_leads)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    try:
        with collector.get_db() as db:
            db.execute("UPDATE leads SET status='contacted' WHERE id=?", (lead_id,))

        if scheduler.running:
            try:
                scheduler.add_job(func=background_collect, trigger="date", next_run_time=datetime.now(timezone.utc), max_instances=1)
            except Exception as e:
                print(f"Error adding background job: {e}")

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    collector.setup_db()

    scheduler.add_job(func=background_collect, trigger="interval", hours=24, next_run_time=datetime.now(timezone.utc), max_instances=1)
    scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
