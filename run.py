import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import collector

app = Flask(__name__)
scheduler = BackgroundScheduler()
is_collecting = False

def background_collect():
    global is_collecting
    if is_collecting:
        return
    is_collecting = True
    try:
        collector.collect_leads()
    finally:
        is_collecting = False

scheduler.add_job(func=background_collect, trigger="interval", hours=24, next_run_time=datetime.now(), max_instances=1)
scheduler.start()


@app.route('/api/leads', methods=['GET'])
def get_leads():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    try:
        with collector.get_db(db_path) as conn:
            cursor = conn.execute("SELECT id, name, type, city, phone FROM leads WHERE contacted = 0")
            leads = [dict(row) for row in cursor.fetchall()]
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_lead():
    db_path = getattr(collector, 'DB_PATH', 'leads.db')
    data = request.json
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({"error": "Missing lead ID"}), 400

    try:
        with collector.get_db(db_path) as conn:
            conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

            # Check remaining uncontacted leads
            cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0")
            remaining = cursor.fetchone()[0]

            if remaining < 5 and scheduler.running:
                try:
                    scheduler.add_job(func=background_collect, next_run_time=datetime.now(), max_instances=1)
                except Exception:
                    pass

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    # For security, only allow specific files explicitly or inside static folder
    if path in ['style.css', 'app.js', 'index.html', 'dashboard.html']:
        return send_from_directory('.', path)
    return send_from_directory('static', path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
