import sqlite3
import threading
from contextlib import contextmanager
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__, static_folder='static')
DATABASE = 'leads.db'

@contextmanager
def get_db(db_path=DATABASE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db(db_path=DATABASE):
    with get_db(db_path) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    with get_db() as db:
        cursor = db.execute('SELECT * FROM leads WHERE contacted = FALSE ORDER BY created_at DESC')
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as db:
        total = db.execute('SELECT COUNT(*) as count FROM leads').fetchone()['count']
        contacted = db.execute('SELECT COUNT(*) as count FROM leads WHERE contacted = TRUE').fetchone()['count']
        new = db.execute('SELECT COUNT(*) as count FROM leads WHERE contacted = FALSE').fetchone()['count']
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new
    })

is_collecting = False

def run_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'ID required'}), 400

    with get_db() as db:
        db.execute('UPDATE leads SET contacted = TRUE WHERE id = ?', (lead_id,))

    # Trigger background collection
    threading.Thread(target=run_collection).start()

    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()

    from datetime import datetime
    scheduler = BackgroundScheduler()
    # Trigger immediately on startup, then every 24 hours
    scheduler.add_job(func=run_collection, trigger="interval", hours=24, next_run_time=datetime.now(), max_instances=1)
    scheduler.start()

    try:
        # debug=False prevents duplicate scheduler
        app.run(debug=False, port=5000)
    finally:
        scheduler.shutdown()
