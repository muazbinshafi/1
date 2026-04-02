from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import db
import collector
import threading

app = Flask(__name__)

# Initialize DB
db.init_db()

# Scheduler for automatic lead collection
scheduler = BackgroundScheduler()
scheduler.add_job(func=collector.collect_leads, trigger="interval", hours=2, max_instances=1)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = db.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        db.mark_contacted(lead_id)

        # Trigger background collection if we are running low or just periodically
        # Here we just run it asynchronously
        threading.Thread(target=collector.collect_leads).start()

        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Missing ID'}), 400

if __name__ == '__main__':
    # Start scheduler
    scheduler.start()

    # Run initial collection in background
    threading.Thread(target=collector.collect_leads).start()

    # Run Flask
    app.run(debug=False, host='0.0.0.0', port=5000)
