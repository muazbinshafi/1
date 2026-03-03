from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_leads, init_db
import logging

# Disable Flask logger to clean up output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
scheduler = BackgroundScheduler()

# Global state to prevent duplicate scraping runs
is_collecting = False
is_collecting_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect('leads.db')
    conn.row_factory = sqlite3.Row
    return conn

def trigger_collection():
    global is_collecting
    with is_collecting_lock:
        if is_collecting:
            print("Collection already running.")
            return
        is_collecting = True

    try:
        print("Starting scheduled lead collection...")
        collect_leads()
    finally:
        with is_collecting_lock:
            is_collecting = False
            print("Lead collection finished.")

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(lead) for lead in leads])

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'contacted': contacted, 'new': new})

@app.route('/api/mark_contacted/<int:lead_id>', methods=['POST'])
def mark_contacted(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

    # Trigger collection in the background if needed
    thread = threading.Thread(target=trigger_collection)
    thread.start()

    return jsonify({'success': True})

if __name__ == '__main__':
    # Initialize DB when app starts
    init_db()

    # Do an initial run at startup
    trigger_collection()

    # Setup scheduler for automatic hourly collection, max_instances=1
    scheduler.add_job(func=trigger_collection, trigger="interval", hours=1, id="collect_leads_job", replace_existing=True, max_instances=1)
    scheduler.start()

    # Run server without debug mode to avoid duplicate jobs and security risks
    app.run(debug=False, port=5000)
