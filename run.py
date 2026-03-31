from flask import Flask, jsonify, request, render_template, send_from_directory
import threading
import time
from database import init_db, get_db
import collector
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Track if scraping is currently active
is_collecting = False

@app.route('/')
def serve_dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    try:
        leads = collector.get_uncontacted_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    try:
        stats = collector.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    lead_id = data.get('id')

    if not lead_id:
        return jsonify({"error": "Lead ID is required"}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": "Lead not found"}), 404

        # Trigger background collection if not already collecting
        trigger_collection()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def trigger_collection():
    global is_collecting
    if not is_collecting:
        # Start a background thread to collect more leads
        threading.Thread(target=background_collect_task).start()

def background_collect_task():
    global is_collecting
    is_collecting = True
    try:
        print("Starting background lead collection...")
        collector.collect_leads()
        print("Background lead collection finished.")
    except Exception as e:
        print(f"Error in background collection: {e}")
    finally:
        is_collecting = False

if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Trigger initial collection
    trigger_collection()

    # Configure APScheduler for periodic collection
    scheduler = BackgroundScheduler()
    # Schedule every 6 hours
    scheduler.add_job(func=trigger_collection, trigger="interval", hours=6, id='collect_leads_job')
    scheduler.start()

    try:
        # Run the application
        app.run(debug=False, port=5000)
    finally:
        scheduler.shutdown()
