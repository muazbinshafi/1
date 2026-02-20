from flask import Flask, render_template, jsonify, request
from .models import db, Lead, init_db
from .collector import collect_leads
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB with app
init_db(app)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

def scheduled_collection():
    with app.app_context():
        logging.info("Starting scheduled lead collection...")
        new_leads = collect_leads()
        count = 0
        for lead_data in new_leads:
            exists = Lead.query.filter_by(phone=lead_data['phone']).first()
            if not exists:
                lead = Lead(
                    name=lead_data['name'],
                    type=lead_data['type'],
                    city=lead_data['city'],
                    phone=lead_data['phone'],
                    website=lead_data['website']
                )
                db.session.add(lead)
                count += 1
        db.session.commit()
        logging.info(f"Scheduled collection finished. Added {count} new leads.")

scheduler.add_job(func=scheduled_collection, trigger="interval", hours=24)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = Lead.query.filter(Lead.status != 'contacted').order_by(Lead.created_at.desc()).all()
    return jsonify([lead.to_dict() for lead in leads])

@app.route('/api/leads/<int:lead_id>/contacted', methods=['POST'])
def mark_contacted(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.status = 'contacted'
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/collect', methods=['POST'])
def trigger_collection():
    try:
        scheduled_collection()
        return jsonify({'success': True, 'message': 'Collection completed.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
