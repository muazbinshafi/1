from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from collector import LeadCollector

app = Flask(__name__)
collector = LeadCollector()

def scheduled_collection():
    print("Running scheduled lead collection...")
    try:
        collector.collect_leads()
    except Exception as e:
        print(f"Scheduled collection failed: {e}")

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", hours=24)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = collector.get_leads()
    return jsonify(leads)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = collector.get_stats()
    return jsonify(stats)

@app.route('/api/mark_contacted', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        collector.mark_contacted(lead_id)

        # Auto-replenish leads if low
        stats = collector.get_stats()
        if stats['new'] < 5:
            print("Low leads detected, auto-collecting...")
            collector.collect_leads()

        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route('/api/collect', methods=['POST'])
def collect():
    count = collector.collect_leads()
    return jsonify({"success": True, "count": count})

if __name__ == '__main__':
    # Initial collection if empty
    if collector.get_stats()['total'] == 0:
        collector.collect_leads()
    app.run(host='0.0.0.0', port=5000)
