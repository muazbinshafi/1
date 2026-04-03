import os
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

# Scheduler configuration
scheduler = BackgroundScheduler()

# We only add the job if we are in the main process (avoids duplicate jobs with Werkzeug reloder if debug was on)
if not scheduler.get_jobs():
    scheduler.add_job(func=collector.collect_leads, trigger="interval", minutes=60, max_instances=1, id='collect_leads_job')
    scheduler.start()

# Make sure the db is initialized
collector.init_db()


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/leads', methods=['GET'])
def get_leads():
    try:
        leads = collector.get_uncontacted_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = collector.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/contact', methods=['POST'])
def contact_lead():
    try:
        data = request.get_json()
        lead_id = data.get('id')
        if not lead_id:
            return jsonify({'error': 'Lead ID is required'}), 400

        collector.mark_contacted(lead_id)

        # Optionally trigger background job after mark if not running already
        try:
             # Run asynchronously or just call it directly since it might block.
             # APScheduler handles overlapping. We will trigger the job by id
             scheduler.get_job('collect_leads_job').modify(next_run_time=None) # run immediately next time
        except Exception:
            pass

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Get port from environment or fallback to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port)
