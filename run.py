import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__, static_folder='static')

# Initialize DB on startup
collector.init_db()

# Scheduler state
is_collecting = False

def do_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()

@app.route('/')
def index():
    # Provide a way to get to the dashboard if needed, or just serve it directly if desired.
    # The portfolio index.html is in the root directory. We'll serve the portfolio for /
    # and dashboard for /dashboard
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return send_from_directory('static', 'dashboard.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('static', 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    # This serves things like CSS/JS from static dynamically via catch-all as per memory
    # Check if the file is in static
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    # Safely serve ONLY specified root UI assets if requested (avoid directory traversal / disclosure)
    elif path in ['style.css', 'app.js', 'index.html'] and os.path.exists(path):
        return send_from_directory('.', path)
    return "Not Found", 404

@app.route('/api/leads', methods=['GET'])
def get_leads():
    # allow tests to inject DB path safely via getattr
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with getattr(collector, 'get_db')() as conn:
        leads_cur = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        leads = [dict(row) for row in leads_cur.fetchall()]

        analytics_cur = conn.execute('''
            SELECT
                COUNT(*) as total_leads,
                SUM(CASE WHEN contacted = 1 THEN 1 ELSE 0 END) as contacted_leads
            FROM leads
        ''')
        analytics = dict(analytics_cur.fetchone())

    return jsonify({'leads': leads, 'analytics': analytics})

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with getattr(collector, 'get_db')() as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger a new background collection job
    if scheduler.running:
        try:
            scheduler.add_job(func=do_collect, trigger='date', run_date=datetime.now())
        except Exception as e:
            print(f"Error adding job: {e}")

    return jsonify({'success': True})

if __name__ == '__main__':
    # Start scheduler
    if not scheduler.running:
        scheduler.add_job(func=do_collect, trigger='interval', hours=24, next_run_time=datetime.now(), max_instances=1)
        scheduler.start()

    # run backend
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
