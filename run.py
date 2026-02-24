from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker
from models import Lead, get_engine, init_db
import collector
import atexit
import datetime

app = Flask(__name__)

# Initialize DB if not exists
init_db()

engine = get_engine()
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    session = get_db_session()
    try:
        leads = session.query(Lead).filter_by(status='new').order_by(Lead.created_at.desc()).all()
        return jsonify([lead.to_dict() for lead in leads])
    finally:
        session.close()

@app.route('/api/leads/<int:lead_id>/contacted', methods=['POST'])
def mark_contacted(lead_id):
    session = get_db_session()
    try:
        lead = session.query(Lead).get(lead_id)
        if lead:
            lead.status = 'contacted'
            session.commit()
            return jsonify({'success': True, 'message': 'Lead marked as contacted'})
        return jsonify({'success': False, 'message': 'Lead not found'}), 404
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    session = get_db_session()
    try:
        total = session.query(Lead).count()
        new_leads = session.query(Lead).filter_by(status='new').count()
        contacted = session.query(Lead).filter_by(status='contacted').count()
        return jsonify({
            'total': total,
            'new': new_leads,
            'contacted': contacted
        })
    finally:
        session.close()

def check_and_replenish_leads():
    """
    Checks if new leads are low (< 5) and triggers collection.
    """
    session = get_db_session()
    try:
        count = session.query(Lead).filter_by(status='new').count()
        if count < 5:
            print(f"Low leads ({count}), triggering collection...")
            collector.collect_leads(city="Bahawalpur", limit=5)
    except Exception as e:
        print(f"Error in scheduler: {e}")
    finally:
        session.close()

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_replenish_leads, trigger="interval", seconds=60)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
