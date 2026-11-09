from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class StartIntakeRequest(BaseModel):
    patient_name: str = Field(..., example="Maria Rodriguez")
    patient_age: Optional[int] = Field(None, example=48)
    patient_gender: Optional[str] = Field(None, example="Female")
    preferred_language: str = Field(default="English", example="Spanish")
    mrn: Optional[str] = Field(None, example="MRN-84920")
    intake_source: Optional[str] = Field(default="web_kiosk", example="web_kiosk")

class IntakeSessionResponse(BaseModel):
    id: int
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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SendMessageRequest(BaseModel):
    message: str = Field(..., example="Tengo un dolor fuerte en el pecho que se me va al brazo izquierdo desde hace dos horas.")
    is_voice: bool = Field(default=False)
    language: Optional[str] = None

class RedFlagAlert(BaseModel):
    flag_type: str  # CARDIAC_ALERT, STROKE_ALERT, RESPIRATORY_DISTRESS, ANAPHYLAXIS, SEVERE_SEPSIS, ACUTE_TRAUMA
    severity: str   # CRITICAL, HIGH, MODERATE
    rationale: str
    recommended_action: str

class SendMessageResponse(BaseModel):
    ai_response: str
    ai_response_translated: Optional[str] = None  # English translation if spoken in non-English
    patient_message_original: str
    patient_message_translated: Optional[str] = None
    red_flags: List[RedFlagAlert] = []
    triage_level: str  # EMERGENCY, URGENT, ROUTINE
    triage_score: int
    suggested_followups: List[str] = []
    is_emergency: bool = False

class ChatMessageItem(BaseModel):
    id: int
    session_id: str
    sender: str
    language: str
    original_text: str
    translated_text: Optional[str]
    is_voice: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CompleteIntakeResponse(BaseModel):
    session_id: str
    status: str
    triage_level: str
    has_red_flags: bool
    summary_id: int
    message: str

