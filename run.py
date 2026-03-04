import os
import atexit
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import database
import collector

app = Flask(__name__)

# Initialize DB on start
database.init_db()

# Scheduler setup to prevent concurrent execution
is_collecting = False

def scheduled_collection():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        print("Running scheduled lead collection...")
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_collection, trigger="interval", seconds=60, max_instances=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/leads", methods=["GET"])
def get_leads():
    leads = database.get_uncontacted_leads()
    return jsonify(leads)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    stats = database.get_stats()
    return jsonify(stats)

@app.route("/api/leads/<int:lead_id>/contact", methods=["POST"])
def contact_lead(lead_id):
    database.mark_contacted(lead_id)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
