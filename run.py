import sqlite3
import logging
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "leads.db"
is_collecting = False

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            type TEXT,
            city TEXT,
            phone TEXT,
            contacted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_leads(leads, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for lead in leads:
        # Check if already exists to prevent duplicates (simple check by name and phone)
        c.execute("SELECT id FROM leads WHERE business_name = ? AND phone = ?", (lead['business_name'], lead['phone']))
        if not c.fetchone():
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
    conn.commit()
    conn.close()

def collect_leads():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        new_leads = collector.collect_leads_sync()
        if new_leads:
            save_leads(new_leads)
    finally:
        is_collecting = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
    new_leads = c.fetchone()[0]
    conn.close()

    return jsonify({
        "total": total,
        "contacted": contacted,
        "new": new_leads
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No ID provided"}), 400

if __name__ == '__main__':
    init_db()

    # Pre-populate with some initial leads if empty
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    if c.fetchone()[0] == 0:
        logger.info("Database empty, collecting initial leads...")
        collect_leads()
    conn.close()

    # Schedule lead collection
    scheduler = BackgroundScheduler()
    # Run every 5 minutes in a background thread, max 1 instance
    scheduler.add_job(func=collect_leads, trigger="interval", minutes=5, max_instances=1)
    scheduler.start()

    # Run Flask app
    try:
        app.run(debug=False, port=5000, host='0.0.0.0')
    finally:
        scheduler.shutdown()
