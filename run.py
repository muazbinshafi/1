import sqlite3
import logging
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "leads.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
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
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")
    finally:
        conn.close()

init_db()

app = Flask(__name__, static_folder="static")
is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        logger.info("Collection already in progress. Skipping.")
        return

    is_collecting = True
    try:
        logger.info("Starting scheduled lead collection...")
        leads = collector.collect_leads()

        conn = get_db_connection()
        cursor = conn.cursor()

        for lead in leads:
            cursor.execute("SELECT id FROM leads WHERE business_name = ? AND city = ?",
                           (lead['business_name'], lead['city']))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO leads (business_name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
        conn.commit()
        conn.close()
        logger.info("Lead collection completed and saved to DB.")
    except Exception as e:
        logger.error(f"Error during scheduled collection: {e}")
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

@app.route('/')
def serve_dashboard():
    return app.send_static_file('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
    new_leads = cursor.fetchone()[0]
    conn.close()
    return jsonify({"total": total, "contacted": contacted, "new": new_leads})

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Lead ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected == 0:
        return jsonify({"error": "Lead not found"}), 404

    return jsonify({"success": True})

if __name__ == '__main__':
    # Initial collection on startup if needed, here we'll let scheduler handle or manual trigger
    # scheduled_collection()
    app.run(debug=False, port=5000, use_reloader=False)
