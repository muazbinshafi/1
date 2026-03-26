import os
import sqlite3
import random
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_db, init_db
import collector

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Global flag to prevent concurrent scraping jobs
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

# Ensure the database exists
init_db()

# Setup scheduler for background data collection
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

# Serve index.html from root
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM leads
            WHERE contacted = 0
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        leads = [dict(row) for row in rows]
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM leads")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as contacted FROM leads WHERE contacted = 1")
        contacted = cursor.fetchone()['contacted']

        cursor.execute("SELECT COUNT(*) as new FROM leads WHERE contacted = 0")
        new_leads = cursor.fetchone()['new']

    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

    # Trigger collection of new leads if needed
    try:
        if not is_collecting:
            scheduler.add_job(func=scheduled_collection, max_instances=1)
    except Exception as e:
        print(f"Error triggering new collection: {e}")

    return jsonify({'success': True})

if __name__ == '__main__':
    # Initial leads collection when the server starts
    collector.collect_leads()

    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
