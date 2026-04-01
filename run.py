import os
import sqlite3
from contextlib import contextmanager
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
DB_PATH = 'leads.db'
is_collecting = False

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@contextmanager
def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    with get_db() as conn:
        leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    return jsonify([dict(lead) for lead in leads])

@app.route('/api/stats', methods=['GET'])
def api_stats():
    with get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = total - contacted
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new
    })

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID required'}), 400

    with get_db() as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger new lead collection async using scheduler
    if scheduler:
        scheduler.add_job(func=collect_job)

    return jsonify({'success': True})

def collect_job():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()

if __name__ == '__main__':
    init_db()
    scheduler.add_job(func=collect_job, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    # Run the initial collection
    scheduler.add_job(func=collect_job)

    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
