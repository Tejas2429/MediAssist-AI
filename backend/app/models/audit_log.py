from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)  # VIEW_PATIENT, EXPORT_RECORD, UPDATE_SOAP, ACKNOWLEDGE_RED_FLAG
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

