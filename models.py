from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)  # 'Clinic', 'Store', 'Service'
    city = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    website = Column(String, nullable=True)
    status = Column(String, default='new')  # 'new', 'contacted'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'business_type': self.business_type,
            'city': self.city,
            'phone': self.phone,
            'website': self.website,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

def get_engine():
    return create_engine('sqlite:///leads.db')

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
