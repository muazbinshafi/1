from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_active_leads, mark_lead_contacted, get_stats
from collector import collect_leads
import threading

app = Flask(__name__)

# Initialize DB on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_get_leads():
    leads = get_active_leads()
    return jsonify(leads)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('lead_id')
    if lead_id:
        mark_lead_contacted('leads.db', lead_id)
        return jsonify({'status': 'success', 'message': 'Lead marked as contacted'})
    return jsonify({'status': 'error', 'message': 'Lead ID not provided'}), 400

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    stats = get_stats()
    return jsonify(stats)

# Set up the APScheduler for background task
scheduler = BackgroundScheduler()
# Run it every 2 minutes for testing (can adjust to hours later)
scheduler.add_job(func=collect_leads, trigger="interval", minutes=2, max_instances=1)
scheduler.start()

if __name__ == '__main__':
    # Initial collection on startup (in a background thread to not block Flask startup)
    threading.Thread(target=collect_leads).start()

    # Run the Flask app
    app.run(debug=False, port=5000)
