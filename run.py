from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
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
    except Exception as e:
        print(f"Error in background collection: {e}")
    finally:
        is_collecting = False

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    # When testing, we need to make sure we use the same db
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    leads = collector.get_uncontacted_leads(db_path)
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    stats = collector.get_stats(db_path)
    return jsonify(stats)

scheduler = BackgroundScheduler()

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    lead_id = data.get('id')
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    if lead_id is not None:
        collector.mark_contacted(lead_id, db_path)
        # trigger a new collection
        if scheduler.running:
            scheduler.add_job(func=scheduled_collection, trigger="date", run_date=datetime.now())
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Lead ID missing"}), 400

if __name__ == '__main__':
    collector.init_db()

    scheduler.add_job(func=scheduled_collection, trigger="interval", hours=1, max_instances=1)
    scheduler.add_job(func=scheduled_collection, trigger="date", run_date=datetime.now(), max_instances=1)
    scheduler.start()

    try:
        app.run(debug=False, port=5000)
    except (KeyboardInterrupt, SystemExit):
        pass
