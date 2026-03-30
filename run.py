import os
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import db
import collector

app = Flask(__name__)

# Initialize DB on startup
db.init_db()

# Global flag for preventing concurrent scraping
is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

# Setup background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, id='scrape_job', replace_existing=True, max_instances=1)

# Start scheduler only if it's the main thread in Werkzeug or if Werkzeug isn't used
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler.start()

# Also run an initial collection immediately (in background)
import threading
threading.Thread(target=scheduled_collection, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    with db.get_db() as conn:
        cursor = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with db.get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'No ID provided'}), 400

    with db.get_db() as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger a new background collection when a lead is marked as contacted
    threading.Thread(target=scheduled_collection, daemon=True).start()

    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port)
