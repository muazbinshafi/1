from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
DB_PATH = getattr(collector, 'DB_PATH', 'leads.db')
collector.init_db(DB_PATH)

is_collecting = False

def background_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads(DB_PATH)
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
if not scheduler.running:
    scheduler.start()
    try:
        scheduler.add_job(func=background_collect, trigger="interval", hours=24, id='collect_job', replace_existing=True, next_run_time=datetime.now())
    except Exception as e:
        print(f"Scheduler error: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    allowed_files = ['style.css', 'app.js', 'index.html', 'dashboard.html']
    if path in allowed_files:
        return send_from_directory('.', path)
    if path.startswith('static/'):
        return send_from_directory('.', path)
    return "Not found", 404

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = collector.get_uncontacted_leads(DB_PATH)
    return jsonify({'leads': leads})

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID required'}), 400

    with collector.get_db(DB_PATH) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
        conn.execute('INSERT INTO leads_log (event, lead_id) VALUES (?, ?)', ('contacted', lead_id))

    # Trigger new collection if scheduler is running
    if scheduler.running:
        try:
            scheduler.add_job(func=background_collect, id=f'collect_job_{datetime.now().timestamp()}', replace_existing=True)
        except Exception as e:
            print(f"Error triggering new collection: {e}")

    return jsonify({'success': True})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    with collector.get_db(DB_PATH) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    return jsonify({
        'total': total,
        'contacted': contacted,
        'pending': total - contacted
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
