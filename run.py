import os
import sqlite3
import logging
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from collector import init_db, collect_leads

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure DB is initialized before first request
init_db()

def get_db_connection():
    conn = sqlite3.connect('leads.db')
    conn.row_factory = sqlite3.Row
    return conn

is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        logger.info("Collection already in progress. Skipping scheduled run.")
        return

    is_collecting = True
    try:
        collect_leads()
    except Exception as e:
        logger.error(f"Error in scheduled collection: {e}")
    finally:
        is_collecting = False

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

# Initial collection immediately on startup (in a separate thread so it doesn't block Flask startup)
# But we only want to do this if we aren't reloading in debug mode, or it'll run multiple times.
import threading
threading.Thread(target=scheduled_collection, daemon=True).start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in leads])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new_leads = total - contacted
    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/leads/<int:lead_id>/contact', methods=['POST'])
def mark_contacted(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        scheduler.shutdown()
