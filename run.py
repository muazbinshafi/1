from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import threading
from collector import collect_leads, init_db

app = Flask(__name__)

is_collecting = False

def background_collect(db_name='leads.db'):
    global is_collecting
    if not is_collecting:
        is_collecting = True
        try:
            collect_leads(db_name)
        finally:
            is_collecting = False

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads')
def api_leads():
    conn = sqlite3.connect('leads.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC')
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(leads)

@app.route('/api/stats')
def api_stats():
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leads')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
    contacted = cursor.fetchone()[0]
    new = total - contacted
    conn.close()
    return jsonify({'total': total, 'contacted': contacted, 'new': new})

@app.route('/api/contacted/<int:id>', methods=['POST'])
def api_contacted(id):
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    # Trigger background collection of new leads
    thread = threading.Thread(target=background_collect, args=('leads.db',))
    thread.start()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db('leads.db')
    # Pre-populate database if empty
    background_collect('leads.db')

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=background_collect, trigger="interval", seconds=3600, max_instances=1)
    scheduler.start()

    # Run the server
    try:
        app.run(debug=False, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
