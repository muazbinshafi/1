import os
import db
import collector
from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Ensure DB is initialized
db.init_db()

# Setup Scheduler for background lead collection
scheduler = BackgroundScheduler()
# Collect leads periodically (e.g., every 60 minutes)
# We set max_instances=1 to ensure no overlaps
scheduler.add_job(func=collector.collect_leads, trigger="interval", minutes=60, max_instances=1)
# Start scheduler
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    # Avoid duplicate scheduler execution in debug mode
    scheduler.start()

# Do an initial run on startup to populate data immediately
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    # Run it in a non-blocking way using the scheduler
    scheduler.add_job(func=collector.collect_leads, trigger='date')

@app.route('/')
def index():
    """Renders the main dashboard."""
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_get_leads():
    """Returns a list of uncontacted leads as JSON."""
    leads = db.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Returns lead statistics as JSON."""
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def api_mark_contacted():
    """Marks a lead as contacted in the database."""
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'error': 'Lead ID is required'}), 400

    lead_id = data['id']
    db.mark_lead_contacted(lead_id)

    # Optionally, trigger a new collection if running low on leads
    stats = db.get_stats()
    if stats['new_leads'] < 5:
        # Schedule immediate collection
        scheduler.add_job(func=collector.collect_leads, trigger='date')

    return jsonify({'success': True, 'message': 'Lead marked as contacted'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)