import sqlite3
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import threading

app = Flask(__name__)

# Global flag to prevent concurrent scraping jobs
is_collecting = False
collect_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect('leads.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
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
    conn.commit()
    conn.close()

def run_collector():
    global is_collecting
    with collect_lock:
        if is_collecting:
            print("Collection already in progress.")
            return
        is_collecting = True

    try:
        from collector import collect_leads
        print("Starting scheduled lead collection...")
        collect_leads()
        print("Lead collection finished.")
    except Exception as e:
        print(f"Error during lead collection: {e}")
    finally:
        with collect_lock:
            is_collecting = False

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads')
def api_leads():
    conn = get_db_connection()
    # Fetch only non-contacted leads
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in leads])

@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': total - contacted
    })

@app.route('/api/leads/<int:lead_id>/contact', methods=['POST'])
def api_contact_lead(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()

    # Configure background scheduler
    scheduler = BackgroundScheduler()
    # Run once right away on startup if no leads exist (or just generally to bootstrap)
    # Then schedule every 1 hour (adjust as necessary)
    scheduler.add_job(func=run_collector, trigger="interval", hours=1, max_instances=1)
    scheduler.start()

    # Trigger initial collection
    threading.Thread(target=run_collector).start()

    # Disable debug mode to prevent scheduler duplication and security issues
    app.run(debug=False, port=5000, host='0.0.0.0', use_reloader=False)
