import os
import sqlite3
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_leads, init_db, DB_FILE

app = Flask(__name__)

# Initialize DB on startup
init_db()

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=collect_leads, trigger="interval", minutes=60)
scheduler.start()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads')
def api_leads():
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in leads])

@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new_leads = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'contacted': contacted,
        'new': new_leads
    })

@app.route('/api/leads/<int:lead_id>/contact', methods=['POST'])
def mark_contacted(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

    # Trigger a new lead collection immediately to find fresh leads
    # using a background job to avoid blocking the API response
    scheduler.add_job(func=collect_leads)

    return jsonify({'success': True})

if __name__ == '__main__':
    # Initial collection on startup
    collect_leads()
    app.run(debug=False, port=5000, host='0.0.0.0')
