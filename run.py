from flask import Flask, render_template, jsonify, request
import db
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
        collector.collect_leads()
    finally:
        is_collecting = False

# Init scheduler
scheduler = BackgroundScheduler()
# Run collection every hour
scheduler.add_job(func=scheduled_collection, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

@app.before_request
def before_request():
    db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    leads = db.get_uncontacted_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def api_stats():
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('lead_id')
    if lead_id:
        success = db.mark_contacted(lead_id)
        return jsonify({'success': success})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    # Initial collection on startup
    import threading
    threading.Thread(target=scheduled_collection).start()

    # Run server
    app.run(debug=False, host='0.0.0.0', port=5000)
