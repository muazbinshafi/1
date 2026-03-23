import os
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import collector
import time

app = Flask(__name__)

# Endpoints
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    try:
        leads = collector.get_uncontacted_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    try:
        stats = collector.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('lead_id')
    if lead_id:
        try:
            collector.mark_contacted(lead_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'No lead_id provided'}), 400


if __name__ == '__main__':
    # Initial data collection
    stats = collector.get_stats()
    if stats['total'] == 0:
        # Run synchronous mock generation to guarantee UI has data for tests
        print("No leads found in DB. Generating mock data for initial load...")
        collector.generate_mock_leads()

    # Setup scheduler for background collection
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=collector.collect_leads, trigger="interval", hours=1, max_instances=1)
    scheduler.start()

    # Determine port
    port = int(os.environ.get("PORT", 5000))

    try:
        # debug=False is important to avoid APScheduler duplicating tasks in development
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        scheduler.shutdown()
