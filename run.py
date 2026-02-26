import sqlite3
import datetime
import logging
import atexit
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_leads

# Initialize Flask App
app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'leads.db'

def init_db():
    """Initialize the SQLite database with the leads table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
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
    conn.commit()
    conn.close()

def save_leads(leads):
    """Save a list of leads to the database, skipping duplicates."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    new_count = 0
    for lead in leads:
        try:
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
            new_count += 1
        except sqlite3.IntegrityError:
            # Duplicate phone number, skip
            pass
    conn.commit()
    conn.close()
    if new_count > 0:
        logger.info(f"Saved {new_count} new leads to database.")

def scheduled_collection():
    """Task to be run by the scheduler."""
    with app.app_context():
        logger.info("Running scheduled lead collection...")
        leads = collect_leads()
        save_leads(leads)

# Initialize Database
init_db()

# Setup Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=5)
scheduler.start()

# Ensure scheduler shuts down
atexit.register(lambda: scheduler.shutdown())

def initial_collection():
    """Run an initial collection if the database is empty."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    count = c.fetchone()[0]
    conn.close()

    if count == 0:
        logger.info("Database is empty. Running initial collection...")
        leads = collect_leads()
        save_leads(leads)

# Check and run initial collection
initial_collection()

# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    """Return all uncontacted leads."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    rows = c.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    """Return dashboard statistics."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
    new_leads = c.fetchone()[0]

    conn.close()
    return jsonify({'total': total, 'contacted': contacted, 'new': new_leads})

@app.route('/api/contacted/<int:id>', methods=['POST'])
def mark_contacted(id):
    """Mark a lead as contacted (soft delete)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    # Run the app
    # Changed to debug=False for production readiness as per memory and context
    app.run(debug=False, host='0.0.0.0', port=5000)
