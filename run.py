from flask import Flask, render_template, jsonify, request
from database import init_db, get_active_leads, mark_lead_contacted, get_lead_count, get_stats_data
from apscheduler.schedulers.background import BackgroundScheduler
import collector
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

scheduler = BackgroundScheduler()

# Scheduler Task
def check_and_replenish_leads():
    logger.info("Checking lead count...")
    with app.app_context():
        try:
            count = get_lead_count()
            logger.info(f"Current active leads: {count}")
            if count < 5:
                logger.info("Low leads! Triggering collector...")
                collector.collect_leads(limit=5)
                logger.info("Collection complete.")
        except Exception as e:
            logger.error(f"Error in scheduler task: {e}")

# Initialize Scheduler
scheduler.add_job(func=check_and_replenish_leads, trigger="interval", minutes=2)
scheduler.start()

# Route for Dashboard
@app.route('/')
def index():
    return render_template('index.html')

# API Route: Get Leads
@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = get_active_leads()
    return jsonify(leads)

# API Route: Get Stats
@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = get_stats_data()
    return jsonify(stats)

# API Route: Mark Contacted
@app.route('/api/leads/<int:lead_id>/contact', methods=['POST'])
def contact_lead(lead_id):
    mark_lead_contacted(lead_id)

    # Trigger immediate check if low
    count = get_lead_count()
    if count < 5:
        # Run ASAP
        scheduler.add_job(check_and_replenish_leads, trigger='date', run_date=datetime.now())

    return jsonify({'success': True, 'message': 'Lead marked as contacted'})

if __name__ == '__main__':
    # Initialize DB
    init_db()

    # Check on startup
    # We can rely on the scheduler or call it directly.
    # Calling it directly might block startup if scraping takes time.
    # Better to add a job to run now.
    scheduler.add_job(check_and_replenish_leads, trigger='date', run_date=datetime.now())

    try:
        # Start app
        # use_reloader=False is important to avoid double scheduler instances
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
