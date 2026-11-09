from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.intake import ChatMessageItem, IntakeSessionResponse, RedFlagAlert

class ClinicalSummaryResponse(BaseModel):
    id: int
    session_id: str
    patient_id: Optional[int]
    chief_complaint: Optional[str]
    hpi: Optional[str]
    onset: Optional[str]
    severity_scale: int
    current_medications: Any
    allergies: Any
    review_of_systems: Any
    red_flags_detected: List[Dict[str, Any]] = []
    triage_rationale: Optional[str]
    soap_subjective: Optional[str]
    soap_objective: Optional[str]
    soap_assessment: Optional[str]
    soap_plan: Optional[str]
    clinician_notes: Optional[str]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientDetailResponse(BaseModel):
    intake_session: IntakeSessionResponse
    messages: List[ChatMessageItem]
    clinical_summary: Optional[ClinicalSummaryResponse]

class UpdateSoapRequest(BaseModel):
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None
    clinician_notes: Optional[str] = None
    status: Optional[str] = "reviewed"

class UpdateTriageRequest(BaseModel):
    triage_level: str  # EMERGENCY, URGENT, ROUTINE, SELF_CARE
    triage_score: int
    rationale: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    total_intakes_today: int
    active_in_queue: int
    critical_red_flags: int
    urgent_triages: int
    routine_triages: int
    reviewed_count: int
    average_wait_minutes: int
    languages_breakdown: Dict[str, int]

class QueueItemResponse(BaseModel):
    session_id: str
    patient_name: str
    patient_age: Optional[int]
    patient_gender: Optional[str]
    preferred_language: str
    status: str
    triage_level: str
    triage_score: int
    has_red_flags: bool
    chief_complaint: Optional[str]
    red_flags_count: int
    wait_time_minutes: int
    created_at: datetime

