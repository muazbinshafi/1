from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import database
import collector
import os

app = Flask(__name__)

is_collecting = False

def collect_leads_job():
    global is_collecting
    if is_collecting:
        print("Scraping job is already running.")
        return

    is_collecting = True
    print("Starting periodic lead collection...")
    try:
        added = collector.scrape_leads()
        print(f"Periodic collection finished. Added {added} new leads.")
    except Exception as e:
        print(f"Error during lead collection: {e}")
    finally:
        is_collecting = False

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = database.get_active_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = database.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.json
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({'error': 'No lead ID provided'}), 400

    database.mark_contacted(lead_id)
    return jsonify({'success': True, 'message': 'Lead marked as contacted'})

if __name__ == '__main__':
    database.init_db()

    # Initial data population if empty
    stats = database.get_stats()
    if stats['total'] == 0:
        print("Database empty. Populating initial mock data...")
        collector.scrape_leads()

    scheduler = BackgroundScheduler()
    # Run the collector every hour, but only allow one instance
    scheduler.add_job(func=collect_leads_job, trigger="interval", minutes=60, max_instances=1)
    scheduler.start()

    # Disable debug in "production" to prevent duplicate scheduler jobs
    app.run(host='0.0.0.0', port=5000, debug=False)
