import sqlite3
import logging
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_leads
import os
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
DB_NAME = 'leads.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT,
            city TEXT,
            phone TEXT,
            contacted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def save_leads(leads):
    """Saves a list of lead dictionaries to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    new_count = 0
    for lead in leads:
        # Check for duplicate phone numbers to avoid spamming
        c.execute("SELECT id FROM leads WHERE phone = ?", (lead['phone'],))
        if c.fetchone() is None:
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (lead['name'], lead['type'], lead['city'], lead['phone']))
            new_count += 1
    conn.commit()
    conn.close()
    logging.info(f"Saved {new_count} new leads to database.")

def scheduled_collection():
    """Wrapper to collect and save leads periodically."""
    logging.info("Starting scheduled lead collection...")
    try:
        leads = collect_leads()
        if leads:
            save_leads(leads)
    except Exception as e:
        logging.error(f"Error during scheduled collection: {e}")

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=5)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads_api():
    conn = get_db_connection()
    # Get uncontacted leads, ordered by newest first
    cursor = conn.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats')
def get_stats_api():
    conn = get_db_connection()

    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
    new_leads = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0").fetchone()[0]

    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/contact/<int:lead_id>', methods=['POST'])
def contact_lead_api(lead_id):
    conn = get_db_connection()
    conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    # Initialize DB on start
    init_db()

    # Run an initial collection if the DB is empty or just to ensure we have data immediately
    # For dev purposes, check if DB is empty
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    conn.close()

    if count == 0:
        logging.info("Database empty, running initial collection...")
        scheduled_collection()

    app.run(host='0.0.0.0', port=5000, debug=False)
