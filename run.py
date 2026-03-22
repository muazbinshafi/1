import os
from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
is_collecting = False

def background_collect_leads():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

@app.before_request
def initialize():
    if not getattr(app, '_init_done', False):
        collector.init_db()
        app._init_done = True
        # Run an initial background collection on startup if the database is empty or we just want to ensure we have leads
        if not collector.get_uncontacted_leads():
            background_collect_leads()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    leads = collector.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    stats = collector.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'error': 'Missing id'}), 400

    lead_id = data['id']
    collector.mark_lead_contacted(lead_id)

    # Trigger a background collection if we're running low on leads, or just always do it as instructed
    scheduler = getattr(app, 'scheduler', None)
    if not is_collecting:
        # Instead of calling collect_leads synchronously, maybe schedule it. But the instructions say:
        # "automatically trigger a new background collection for leads via the /api/contact POST endpoint."
        # Background is key.
        from threading import Thread
        Thread(target=background_collect_leads).start()

    return jsonify({'success': True})

if __name__ == '__main__':
    # APScheduler setup
    scheduler = BackgroundScheduler()
    # Schedule collect_leads to run every 12 hours (43200 seconds)
    scheduler.add_job(func=background_collect_leads, trigger="interval", seconds=43200, max_instances=1)
    scheduler.start()

    # Run Flask with debug=False to avoid duplicate schedulers and security risks
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
