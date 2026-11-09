from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, index=True, nullable=False)  # Medical Record Number
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    primary_language = Column(String(50), default="English")
    contact_phone = Column(String(50), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    known_allergies = Column(Text, default="[]")  # JSON or text
    medical_history = Column(Text, default="[]")  # JSON or text
    created_at = Column(DateTime, default=datetime.utcnow)

