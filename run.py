from flask import Flask, render_template, jsonify, request
import collector
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime

app = Flask(__name__)

is_collecting = False

def run_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        db_path = getattr(collector, 'DB_PATH', 'leads.db')
        collector.collect_leads(db_path=db_path)
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=run_collection, trigger="interval", hours=24, next_run_time=datetime.now(), max_instances=1)
scheduler.start()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path=db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC')
        leads = [dict(row) for row in cursor.fetchall()]
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path=db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM leads')
        total = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as contacted FROM leads WHERE contacted = 1')
        contacted = cursor.fetchone()['contacted']

        cursor.execute('SELECT COUNT(*) as new FROM leads WHERE contacted = 0')
        new_leads = cursor.fetchone()['new']

    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'Lead ID is required'}), 400

    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    with collector.get_db(db_path=db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

    # Trigger new background collection if scheduler is running
    if scheduler.running:
        scheduler.add_job(func=run_collection, trigger="date", next_run_time=datetime.now(), max_instances=1)

    return jsonify({'success': True})

if __name__ == '__main__':
    collector.init_db()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
