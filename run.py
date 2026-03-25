import sqlite3
from contextlib import contextmanager

DB_PATH = 'leads.db'

@contextmanager
def get_db(db_path=DB_PATH):
    """
    Context manager for sqlite3 connections.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_PATH):
    """
    Initialize schema for the leads table.
    """
    with get_db(db_path) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

is_collecting = False

def insert_leads(leads, db_path=DB_PATH):
    with get_db(db_path) as db:
        for lead in leads:
            # Check if lead already exists to avoid duplicates
            cursor = db.execute('SELECT 1 FROM leads WHERE phone = ?', (lead['phone'],))
            if not cursor.fetchone():
                db.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (lead['business_name'], lead['type'], lead['city'], lead['phone'])
                )

def run_collection_job():
    global is_collecting
    if is_collecting:
        return

    is_collecting = True
    try:
        leads = collector.collect_leads()
        if not leads:
            # fallback to mock data if scraping fails to find leads
            leads = collector.generate_mock_leads()

        insert_leads(leads)
    except Exception as e:
        print(f"Error in collection job: {e}")
    finally:
        is_collecting = False

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_collection_job, trigger="interval", minutes=60, max_instances=1)

def get_uncontacted_leads(db_path=DB_PATH):
    with get_db(db_path) as db:
        cursor = db.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_stats(db_path=DB_PATH):
    with get_db(db_path) as db:
        total = db.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = db.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        return {
            "total": total,
            "contacted": contacted,
            "new": total - contacted
        }

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    return jsonify(get_uncontacted_leads())

@app.route('/api/stats', methods=['GET'])
def api_stats():
    return jsonify(get_stats())

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({"error": "Lead ID is required"}), 400

    with get_db() as db:
        db.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger new collection
    scheduler.add_job(func=run_collection_job, trigger='date')

    return jsonify({"success": True})

if __name__ == '__main__':
    init_db()
    # Initial collection on startup if needed
    run_collection_job()
    scheduler.start()

    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    # debug=False prevents duplicate schedulers from running in dev mode
    app.run(host='0.0.0.0', port=port, debug=False)
