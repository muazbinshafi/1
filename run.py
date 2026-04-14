from flask import Flask, send_from_directory, jsonify, request
import os
import collector
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='static')

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

@app.route('/')
def index():
    return send_from_directory('static', 'dashboard.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/stats')
def get_stats():
    # Use dynamic db path as mentioned in memory guidelines
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM leads')
        total = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
        contacted = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0')
        new_leads = cur.fetchone()[0]
        return jsonify({
            'total': total,
            'contacted': contacted,
            'new': new_leads
        })
    finally:
        conn.close()

@app.route('/api/leads')
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC')
        rows = cur.fetchall()
        leads = [dict(row) for row in rows]
        return jsonify(leads)
    finally:
        conn.close()

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID required'}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
        conn.commit()

        # Trigger background collection if scheduler is running (will be added next step)
        if 'scheduler' in globals() and scheduler.running:
            if not is_collecting:
                try:
                    scheduler.add_job(id='trigger_collect', func=collector.collect_leads)
                except Exception as e:
                    pass

        return jsonify({'success': True})
    finally:
        conn.close()

if __name__ == '__main__':
    collector.init_db()

    # Run immediate collection on startup
    scheduler.add_job(func=scheduled_collection, trigger='interval', hours=24, next_run_time=datetime.now(), max_instances=1)
    scheduler.start()

    # Disable debug to prevent double scheduler startups
    app.run(host='0.0.0.0', port=5000, debug=False)
