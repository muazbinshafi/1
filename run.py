from flask import Flask, render_template, jsonify, request
import logging
from db import init_db, get_uncontacted_leads, get_stats, mark_lead_contacted
from collector import run_scraper
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Track if scraping is currently running
is_collecting = False

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads_api():
    try:
        leads = get_uncontacted_leads()
        return jsonify({"status": "success", "data": leads}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats_api():
    try:
        stats = get_stats()
        return jsonify({"status": "success", "data": stats}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    try:
        data = request.json
        if not data or 'lead_id' not in data:
            return jsonify({"status": "error", "message": "Missing lead_id"}), 400

        lead_id = data['lead_id']
        success = mark_lead_contacted(lead_id)

        if success:
            return jsonify({"status": "success", "message": "Lead marked as contacted"}), 200
        else:
            return jsonify({"status": "error", "message": "Lead not found or already contacted"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def collect_leads_job():
    global is_collecting
    if is_collecting:
        logging.info("Scraping already in progress. Skipping scheduled job.")
        return

    is_collecting = True
    try:
        logging.info("Scheduled job: Starting lead collection.")
        run_scraper()
    except Exception as e:
        logging.error(f"Scheduled job failed: {e}")
    finally:
        is_collecting = False

if __name__ == '__main__':
    # Initialize Database
    init_db()

    # We will schedule the collection job, but run app immediately so it doesn't block startup

    # Setup Background Scheduler
    scheduler = BackgroundScheduler()
    # Schedule collection every 10 minutes to grab new leads dynamically
    scheduler.add_job(func=collect_leads_job, trigger="interval", minutes=10, max_instances=1)
    scheduler.start()

    try:
        # Run the app
        # Use debug=False to avoid running the scheduler twice
        app.run(host='0.0.0.0', port=5000, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()