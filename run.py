import os
import atexit
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration
app.config['JSON_AS_ASCII'] = False

# Scheduler setup
scheduler = BackgroundScheduler()
is_collecting = False

def scheduled_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        db_path = getattr(collector, 'DB_PATH', 'leads.db')
        collector.collect_leads(db_path)
    finally:
        is_collecting = False

# Schedule background job periodically
scheduler.add_job(func=scheduled_collect, trigger="interval", minutes=60, id='collect_leads_job')

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    collector.init_db(db_path)
    with collector.get_db(db_path) as db:
        cur = db.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        leads = [dict(row) for row in cur.fetchall()]
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    collector.init_db(db_path)
    with collector.get_db(db_path) as db:
        cur = db.execute('SELECT COUNT(*) as count FROM leads')
        total = cur.fetchone()['count']

        cur = db.execute('SELECT COUNT(*) as count FROM leads WHERE contacted = 1')
        contacted = cur.fetchone()['count']

        new_leads = total - contacted

    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as db:
        db.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger collection if scheduler is running
    if scheduler.running:
        try:
            # We add a job that runs immediately
            scheduler.add_job(func=scheduled_collect, next_run_time=datetime.now())
        except Exception as e:
            app.logger.error(f"Failed to schedule immediate collection: {e}")

    return jsonify({'success': True})

def start_scheduler():
    # Start scheduler only if not in testing or if explicitly requested
    if not os.environ.get("WERKZEUG_RUN_MAIN") == "true" and not os.environ.get("TESTING") == "true":
        if not scheduler.running:
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown(wait=False))
            # Run immediately on startup
            scheduler.add_job(func=scheduled_collect, next_run_time=datetime.now())

if __name__ == '__main__':
    start_scheduler()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)