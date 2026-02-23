from flask import Flask, render_template, jsonify, request
import sqlite3
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
DB_NAME = 'leads.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    contacted BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def populate_leads():
    """ collecting leads and saving to DB """
    print("Running scheduled lead collection...")
    leads = collector.collect_leads()
    conn = get_db_connection()
    c = conn.cursor()
    for lead in leads:
        # Check if lead already exists (simple check by phone)
        c.execute("SELECT id FROM leads WHERE phone = ?", (lead['phone'],))
        if c.fetchone() is None:
            c.execute("INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                      (lead['name'], lead['type'], lead['city'], lead['phone']))
    conn.commit()
    conn.close()
    print("Leads replenished.")

def check_and_replenish():
    """ Check if we need more leads """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
    count = c.fetchone()[0]
    conn.close()

    if count < 5:
        print(f"Low lead count ({count}), triggering replenishment...")
        populate_leads()

# Initialize DB
init_db()

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_replenish, trigger="interval", seconds=60)
scheduler.start()

# Ensure scheduler shuts down
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY timestamp DESC').fetchall()
    conn.close()
    return jsonify([dict(lead) for lead in leads])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new_leads = total - contacted
    conn.close()
    return jsonify({'total': total, 'contacted': contacted, 'new': new_leads})

@app.route('/api/leads/<int:lead_id>/contacted', methods=['POST'])
def mark_contacted(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

    # Trigger replenishment check immediately
    check_and_replenish()

    return jsonify({'success': True})

if __name__ == '__main__':
    # Initial population if empty
    check_and_replenish()
    app.run(debug=True, host='0.0.0.0', port=5000)
