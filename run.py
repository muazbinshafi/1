import sqlite3
import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
DATABASE = 'leads.db'
is_collecting = False

def get_db(db_path=DATABASE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DATABASE):
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(business_name, city)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'No lead ID provided'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as total FROM leads')
    total = c.fetchone()['total']

    c.execute('SELECT COUNT(*) as contacted FROM leads WHERE contacted = 1')
    contacted = c.fetchone()['contacted']

    c.execute('SELECT COUNT(*) as new_leads FROM leads WHERE contacted = 0')
    new_leads = c.fetchone()['new_leads']

    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new_leads': new_leads
    })

def collect_data_job():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.run_collector(DATABASE)
    except Exception as e:
        print(f"Error collecting data: {e}")
    finally:
        is_collecting = False

if __name__ == '__main__':
    init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=collect_data_job, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    app.run(debug=False, port=5000)
