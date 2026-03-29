import os
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)

is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        print("Starting scheduled lead collection...")
        collector.collect_leads()
        print("Lead collection completed.")
    except Exception as e:
        print(f"Error in scheduled collection: {e}")
    finally:
        is_collecting = False

# Setup background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
# Only start scheduler if not in debug reload mode
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

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
def mark_contacted():
    try:
        data = request.get_json()
        lead_id = data.get('id')
        if lead_id is None:
            return jsonify({'error': 'Lead ID is required'}), 400

        collector.mark_contacted(lead_id)

        # Trigger background collection if we are low on leads (or after every contact)
        # Using APScheduler to add a one-off job to collect more
        scheduler.add_job(func=scheduled_collection)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize the database on startup
    collector.init_db()
    # Optional: Collect leads initially if db is empty (or just use fallback)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
