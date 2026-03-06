from flask import Flask, jsonify, request
import sqlite3
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_leads, init_db

app = Flask(__name__, static_folder='static', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        logging.info("Collection already in progress, skipping this run.")
        return

    is_collecting = True
    try:
        collect_leads()
    except Exception as e:
        logging.error(f"Error during scheduled collection: {e}")
    finally:
        is_collecting = False

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = init_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
    new_leads = c.fetchone()[0]

    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/contacted/<int:lead_id>', methods=['POST'])
def mark_contacted(lead_id):
    conn = init_db()
    c = conn.cursor()
    c.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    # Initialize DB on startup
    init_db()

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    # Run the initial collection once
    # scheduled_collection()

    # Run Flask app
    try:
        app.run(debug=False, port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
