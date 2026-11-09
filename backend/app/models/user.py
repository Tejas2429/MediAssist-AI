from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="clinician")  # clinician, nurse, admin, triage_officer
    department = Column(String(100), default="General / Triage")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

