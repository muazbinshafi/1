from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import collector

app = Flask(__name__)

is_collecting = False

def run_collector():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        # Use dynamic DB path
        db_path = getattr(collector, 'DB_PATH', 'leads.db')
        collector.collect_leads(db_path)
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()

# Add job to collect leads initially and then every 2 hours
scheduler.add_job(func=run_collector, trigger="interval", hours=2, id='collect_leads_job', max_instances=1, next_run_time=datetime.now())

@app.route('/api/leads', methods=['GET'])
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as conn:
        leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
        return jsonify([dict(lead) for lead in leads])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = total - contacted
        return jsonify({'total': total, 'contacted': contacted, 'new': new})

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger collection
    if scheduler.running:
        try:
            scheduler.add_job(func=run_collector, trigger="date", next_run_time=datetime.now())
        except Exception:
            pass

    return jsonify({'success': True})

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    # We will serve a dashboard html directly
    return send_from_directory('.', 'dashboard.html')

# Make sure we don't start the scheduler in debug/reload mode
if __name__ == '__main__':
    scheduler.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
