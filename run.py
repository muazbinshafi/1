from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import os
import time
from collector import collect_leads_impl

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  business_name TEXT,
                  type TEXT,
                  city TEXT,
                  phone TEXT,
                  contacted INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

is_collecting = False

# Scheduler
def collect_leads():
    global is_collecting
    if is_collecting:
        print("Scraping already in progress. Skipping...")
        return

    is_collecting = True
    try:
        print("Collecting leads...")
        collect_leads_impl()
    finally:
        is_collecting = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=collect_leads, trigger="interval", minutes=60, max_instances=1)
scheduler.start()

# Also run once at startup
scheduler.add_job(func=collect_leads)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads')
def get_leads():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute("SELECT id, business_name, type, city, phone FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [{'id': row[0], 'business_name': row[1], 'type': row[2], 'city': row[3], 'phone': row[4]} for row in c.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = c.fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'contacted': contacted, 'new': total - contacted})

@app.route('/api/contacted', methods=['POST'])
def mark_contacted():
    data = request.json
    lead_id = data.get('id')
    if lead_id:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
        conn.commit()
        conn.close()

        # Trigger an immediate background job to replenish the pool
        scheduler.add_job(func=collect_leads)

        return jsonify({'success': True})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    if not os.path.exists('leads.db'):
        init_db()
    app.run(debug=False, port=5000)
