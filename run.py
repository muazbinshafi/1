from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import collector
import os
import threading

app = Flask(__name__)
is_collecting = False
collect_lock = threading.Lock()

def collect_leads_background():
    global is_collecting
    if collect_lock.acquire(blocking=False):
        try:
            is_collecting = True
            collector.collect_leads_job()
        finally:
            is_collecting = False
            collect_lock.release()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/leads")
def api_leads():
    leads = collector.get_uncontacted_leads()
    return jsonify({"leads": leads})

@app.route("/api/stats")
def api_stats():
    stats = collector.get_stats()
    return jsonify(stats)

@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.json
    lead_id = data.get("id")
    if lead_id:
        collector.mark_contacted(lead_id)
        # Trigger background collection since we contacted a lead
        threading.Thread(target=collect_leads_background).start()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    collector.init_db()

    # Run initial collection
    threading.Thread(target=collect_leads_background).start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=collect_leads_background, trigger="interval", hours=24, max_instances=1)
    scheduler.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
