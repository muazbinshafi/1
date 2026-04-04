import sqlite3
from contextlib import contextmanager
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
DB_PATH = 'leads.db'
is_collecting = False

@contextmanager
def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_PATH):
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def collect_leads():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        leads = collector.scrape_leads()
        if not leads:
            leads = collector.generate_mock_leads()

        with get_db() as conn:
            for lead in leads:
                try:
                    conn.execute('''
                        INSERT INTO leads (business_name, type, city, phone)
                        VALUES (?, ?, ?, ?)
                    ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
                except sqlite3.IntegrityError:
                    pass # Ignore duplicate phone numbers
    except Exception as e:
        print(f"Error during lead collection: {e}")
    finally:
        is_collecting = False

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def stats():
    with get_db(DB_PATH) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new_leads = total - contacted
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new_leads': new_leads
    })

def get_uncontacted_leads(db_path=DB_PATH):
    with get_db(db_path) as conn:
        leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
        return [dict(lead) for lead in leads]

@app.route('/api/leads')
def api_leads():
    leads = get_uncontacted_leads(DB_PATH)
    return jsonify(leads)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'success': False, 'error': 'No lead ID provided'}), 400

    with get_db(DB_PATH) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger background collection if needed (for simplicity, we trigger it synchronously here if queue is empty)
    with get_db(DB_PATH) as conn:
        uncontacted_count = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
        if uncontacted_count < 5 and not is_collecting:
            scheduler.add_job(func=collect_leads, trigger="date")

    return jsonify({'success': True})

scheduler = BackgroundScheduler()
scheduler.add_job(func=collect_leads, trigger="interval", minutes=60, max_instances=1)

if __name__ == '__main__':
    import os
    init_db()
    # Initial collection on startup
    scheduler.add_job(func=collect_leads, trigger="date")
    scheduler.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
