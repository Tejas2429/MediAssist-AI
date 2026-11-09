from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.core.database import Base

class ClinicalSummary(Base):
    __tablename__ = "clinical_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    chief_complaint = Column(Text, nullable=True)
    hpi = Column(Text, nullable=True)  # History of Present Illness
    onset = Column(String(100), nullable=True)
    severity_scale = Column(Integer, default=5)  # 1-10 scale
    
    current_medications = Column(Text, default="[]")  # JSON or bullet list
    allergies = Column(Text, default="[]")  # JSON or bullet list
    review_of_systems = Column(Text, default="{}")  # JSON or structured text
    
    # Red-flags & Triaging
    red_flags_detected = Column(Text, default="[]")  # JSON list of flags with rationales
    triage_rationale = Column(Text, nullable=True)
    
    # Automated Clinician SOAP Note
    soap_subjective = Column(Text, nullable=True)
    soap_objective = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)
    soap_plan = Column(Text, nullable=True)
    
    # Clinician Review
    clinician_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

