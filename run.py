import os
import json
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

import collector
from collector import get_db

app = Flask(__name__)
scheduler = BackgroundScheduler()

is_collecting = False

def run_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

@app.before_request
def setup():
    if not getattr(app, 'initialized', False):
        collector.init_db()
        app.initialized = True

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    path = getattr(collector, 'DB_PATH', 'leads.db')
    with get_db(path) as conn:
        leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    return jsonify([dict(row) for row in leads])

@app.route('/api/stats')
def get_stats():
    path = getattr(collector, 'DB_PATH', 'leads.db')
    with get_db(path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new_leads = total - contacted
    return jsonify({'total': total, 'contacted': contacted, 'new': new_leads})

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')
    path = getattr(collector, 'DB_PATH', 'leads.db')
    if lead_id:
        with get_db(path) as conn:
            conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

        # trigger a new background scraping job
        if scheduler.running:
            scheduler.add_job(run_collection, trigger='date', run_date=datetime.now(), max_instances=1)

        return jsonify({'success': True})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    collector.init_db()
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        scheduler.add_job(
            func=run_collection,
            trigger=IntervalTrigger(minutes=60),
            id='scrape_job',
            name='Scrape DuckDuckGo for Leads',
            replace_existing=True,
            max_instances=1,
            next_run_time=datetime.now()
        )
        scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port)
