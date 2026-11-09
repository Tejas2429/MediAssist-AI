from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from app.core.database import Base

class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    patient_name = Column(String(150), nullable=False)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(30), nullable=True)
    preferred_language = Column(String(50), default="English")
    status = Column(String(50), default="in_progress")  # in_progress, submitted, reviewed, escalated
    triage_level = Column(String(50), default="ROUTINE")  # EMERGENCY, URGENT, ROUTINE, SELF_CARE
    triage_score = Column(Integer, default=4)  # ESI 1 (critical) to 5 (non-urgent)
    has_red_flags = Column(Boolean, default=False)
    chief_complaint = Column(Text, nullable=True)
    intake_source = Column(String(50), default="web_kiosk")  # web_kiosk, mobile, registration_desk
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

