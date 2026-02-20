from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False) # Clinic, Store, Service
    city = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    website = Column(String(100), nullable=True) # Should be None/Empty
    status = Column(String(20), default='new') # new, contacted, archived
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'city': self.city,
            'phone': self.phone,
            'website': self.website,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
