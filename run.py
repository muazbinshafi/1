from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import collector
from datetime import datetime

app = Flask(__name__)
scheduler = BackgroundScheduler()
is_collecting = False

def run_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        db_path = getattr(collector, 'DB_PATH', 'leads.db')
        collector.collect_leads(db_path)
    finally:
        is_collecting = False

# Schedule the collection to run periodically
scheduler.add_job(id='collect_leads_job', func=run_collection, trigger='interval', hours=1, max_instances=1, next_run_time=datetime.now())
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

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
        total = conn.execute('SELECT COUNT(*) as count FROM leads').fetchone()['count']
        contacted = conn.execute('SELECT COUNT(*) as count FROM leads WHERE contacted = 1').fetchone()['count']
        new = total - contacted
        return jsonify({
            'total': total,
            'contacted': contacted,
            'new': new
        })

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger background collection to replenish leads
    if scheduler.running:
        try:
            scheduler.add_job(id=f'collect_leads_job_{datetime.now().timestamp()}', func=run_collection, next_run_time=datetime.now())
        except Exception:
            pass

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(port=5000, debug=False)
