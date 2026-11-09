import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.patient import Patient
from app.models.intake_session import IntakeSession
from app.models.chat_message import ChatMessage
from app.models.clinical_summary import ClinicalSummary
from app.schemas.intake import (
    StartIntakeRequest,
    IntakeSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    ChatMessageItem,
    CompleteIntakeResponse,
    RedFlagAlert
)
from app.services.gemini_service import gemini_service
from app.services.triage_engine import calculate_triage_score

router = APIRouter()

# Multilingual welcome greetings
WELCOME_MESSAGES = {
    "Spanish": "¡Hola, {name}! Soy su asistente médico virtual MediAssist AI. Estoy aquí para ayudarle con su ingreso clínico. ¿Cuál es el motivo principal de su consulta el día de hoy?",
    "Hindi": "नमस्ते {name}! मैं MediAssist AI हूँ, आपका डिजिटल मेडिकल सहायक। आज आपकी क्या समस्या या तकलीफ है?",
    "French": "Bonjour {name} ! Je suis MediAssist AI, votre assistant médical virtuel. Quelle est la raison principale de votre visite aujourd'hui ?",
    "Mandarin": "您好，{name}！我是 MediAssist AI 智能医疗助手。请问您今天感觉哪里不舒服？",
    "Arabic": "مرحباً {name}! أنا MediAssist AI، مساعدك الطبي الافتراضي. ما هي الشكوى الطبية الرئيسية التي تشعر بها اليوم؟",
    "German": "Hallo {name}! Ich bin MediAssist AI, Ihr virtueller medizinischer Assistent. Was führt Sie heute zu uns?",
    "English": "Hello {name}! I am MediAssist AI, your clinical intake companion. What is the main reason or symptom for your visit today?"
}

WELCOME_MESSAGES_EN = {
    "Spanish": "Hello, {name}! I am your MediAssist AI clinical companion. I am here to help with your intake. What is the main reason for your visit today?",
    "Hindi": "Hello {name}! I am MediAssist AI, your digital medical assistant. What problem or discomfort are you experiencing today?",
    "French": "Hello {name}! I am MediAssist AI, your virtual medical companion. What is the main reason for your visit today?",
    "Mandarin": "Hello {name}! I am MediAssist AI. What symptoms or discomfort are you experiencing today?",
    "Arabic": "Hello {name}! I am MediAssist AI, your medical assistant. What is the main symptom you are experiencing today?",
    "German": "Hello {name}! I am MediAssist AI, your clinical intake assistant. What brings you in today?",
    "English": "Hello {name}! I am MediAssist AI, your clinical intake companion. What is the main reason or symptom for your visit today?"
}

@router.post("/start", response_model=IntakeSessionResponse)
async def start_intake(data: StartIntakeRequest, db: AsyncSession = Depends(get_db)):
    session_uuid = str(uuid.uuid4())
    
    # Check or create patient record if MRN provided
    patient_id = None
    if data.mrn:
        result = await db.execute(select(Patient).where(Patient.mrn == data.mrn))
        patient = result.scalars().first()
        if patient:
            patient_id = patient.id
    
    # Create intake session
    session = IntakeSession(
        session_id=session_uuid,
        patient_id=patient_id,
        patient_name=data.patient_name,
        patient_age=data.patient_age,
        patient_gender=data.patient_gender,
        preferred_language=data.preferred_language,
        status="in_progress",
        triage_level="ROUTINE",
        triage_score=4,
        has_red_flags=False,
        chief_complaint=None,
        intake_source=data.intake_source or "web_kiosk"
    )
    db.add(session)
    await db.flush()

    # Create automated initial welcome greeting in patient's preferred language
    lang = data.preferred_language
    greeting_template = WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["English"])
    greeting_en = WELCOME_MESSAGES_EN.get(lang, WELCOME_MESSAGES_EN["English"])
    greeting_text = greeting_template.format(name=data.patient_name)
    greeting_en_text = greeting_en.format(name=data.patient_name)

    initial_msg = ChatMessage(
        session_id=session_uuid,
        sender="ai_assistant",
        language=lang,
        original_text=greeting_text,
        translated_text=greeting_en_text,
        is_voice=False
    )
    db.add(initial_msg)
    await db.commit()
    await db.refresh(session)
    
    return session

@router.post("/{session_id}/message", response_model=SendMessageResponse)
async def send_intake_message(
    session_id: str,
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    # Fetch past dialogue history
    history_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    past_messages = history_res.scalars().all()
    history_list = [
        {"sender": m.sender, "text": m.original_text, "language": m.language}
        for m in past_messages
    ]

    # Generate clinical AI response using Gemini + Red Flag scanner
    response_data = await gemini_service.generate_intake_response(
        patient_name=session.patient_name,
        preferred_language=session.preferred_language,
        conversation_history=history_list,
        new_message=payload.message
    )

    # Record patient's message
    patient_msg = ChatMessage(
        session_id=session_id,
        sender="patient",
        language=session.preferred_language,
        original_text=payload.message,
        translated_text=response_data.get("patient_message_translated", payload.message),
        is_voice=payload.is_voice
    )
    db.add(patient_msg)

    # Record AI's response
    ai_msg = ChatMessage(
        session_id=session_id,
        sender="ai_assistant",
        language=session.preferred_language,
        original_text=response_data["ai_reply"],
        translated_text=response_data.get("ai_reply_en", response_data["ai_reply"]),
        is_voice=False
    )
    db.add(ai_msg)

    # Update session status, triage, and red flag indicators
    red_flags = response_data.get("red_flags", [])
    if red_flags:
        session.has_red_flags = True
        session.triage_level = response_data.get("triage_level", "EMERGENCY")
        session.triage_score = response_data.get("triage_score", 1)
        if response_data.get("is_emergency"):
            session.status = "escalated"
    
    if not session.chief_complaint:
        session.chief_complaint = payload.message[:150]
    
    session.updated_at = datetime.utcnow()
    await db.commit()

    return SendMessageResponse(
        ai_response=response_data["ai_reply"],
        ai_response_translated=response_data.get("ai_reply_en"),
        patient_message_original=payload.message,
        patient_message_translated=response_data.get("patient_message_translated"),
        red_flags=[RedFlagAlert(**f) for f in red_flags],
        triage_level=session.triage_level,
        triage_score=session.triage_score,
        suggested_followups=response_data.get("suggested_followups", []),
        is_emergency=response_data.get("is_emergency", False)
    )

@router.post("/{session_id}/complete", response_model=CompleteIntakeResponse)
async def complete_intake(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    # Fetch all messages
    msgs_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msgs_res.scalars().all()
    message_dicts = [{"sender": m.sender, "text": m.original_text, "language": m.language} for m in messages]

    # Check for existing summary
    summary_res = await db.execute(select(ClinicalSummary).where(ClinicalSummary.session_id == session_id))
    summary = summary_res.scalars().first()

    # Generate or update summary using Gemini
    summary_data = await gemini_service.generate_clinical_summary(
        patient_name=session.patient_name,
        patient_age=session.patient_age,
        patient_gender=session.patient_gender,
        preferred_language=session.preferred_language,
        messages=message_dicts,
        red_flags=[],
        triage_level=session.triage_level
    )

    if not summary:
        summary = ClinicalSummary(
            session_id=session_id,
            patient_id=session.patient_id,
            chief_complaint=summary_data.get("chief_complaint") or session.chief_complaint or "Unspecified discomfort",
            hpi=summary_data.get("hpi"),
            onset=summary_data.get("onset"),
            severity_scale=summary_data.get("severity_scale", 5),
            current_medications=json.dumps(summary_data.get("current_medications", [])),
            allergies=json.dumps(summary_data.get("allergies", [])),
            review_of_systems=json.dumps(summary_data.get("review_of_systems", {})),
            red_flags_detected=json.dumps([]),
            triage_rationale=f"Automated clinical synthesis completed for {session.patient_name}.",
            soap_subjective=summary_data.get("soap_subjective"),
            soap_objective=summary_data.get("soap_objective"),
            soap_assessment=summary_data.get("soap_assessment"),
            soap_plan=summary_data.get("soap_plan")
        )
        db.add(summary)
    else:
        summary.chief_complaint = summary_data.get("chief_complaint") or summary.chief_complaint
        summary.hpi = summary_data.get("hpi") or summary.hpi
        summary.soap_subjective = summary_data.get("soap_subjective") or summary.soap_subjective
        summary.soap_objective = summary_data.get("soap_objective") or summary.soap_objective
        summary.soap_assessment = summary_data.get("soap_assessment") or summary.soap_assessment
        summary.soap_plan = summary_data.get("soap_plan") or summary.soap_plan
        summary.updated_at = datetime.utcnow()

    if session.status != "escalated":
        session.status = "submitted"
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(summary)

    return CompleteIntakeResponse(
        session_id=session_id,
        status=session.status,
        triage_level=session.triage_level,
        has_red_flags=session.has_red_flags,
        summary_id=summary.id,
        message="Patient intake completed and clinical summary successfully prepared for clinician review."
    )

@router.get("/{session_id}/status")
async def get_intake_status(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    msgs_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msgs_res.scalars().all()

    return {
        "session": IntakeSessionResponse.model_validate(session),
        "messages": [ChatMessageItem.model_validate(m) for m in messages]
    }

