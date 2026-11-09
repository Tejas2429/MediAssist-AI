import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.intake_session import IntakeSession
from app.models.chat_message import ChatMessage
from app.models.clinical_summary import ClinicalSummary
from app.models.audit_log import AuditLog
from app.schemas.clinical import (
    DashboardStatsResponse,
    QueueItemResponse,
    PatientDetailResponse,
    ClinicalSummaryResponse,
    UpdateSoapRequest,
    UpdateTriageRequest
)
from app.schemas.intake import IntakeSessionResponse, ChatMessageItem
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    # Optional auth for dashboard view
):
    # Total intakes
    total_res = await db.execute(select(func.count(IntakeSession.id)))
    total_count = total_res.scalar() or 0

    # Active in queue (in_progress, submitted, escalated)
    active_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.status.in_(["submitted", "escalated", "in_progress"]))
    )
    active_count = active_res.scalar() or 0

    # Critical red flags
    red_flags_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.has_red_flags == True)
    )
    red_flags_count = red_flags_res.scalar() or 0

    # Emergency triages
    emerg_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.triage_level == "EMERGENCY")
    )
    emerg_count = emerg_res.scalar() or 0

    # Urgent triages
    urg_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.triage_level == "URGENT")
    )
    urg_count = urg_res.scalar() or 0

    # Routine triages
    routine_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.triage_level.in_(["ROUTINE", "SELF_CARE"]))
    )
    routine_count = routine_res.scalar() or 0

    # Reviewed count
    rev_res = await db.execute(
        select(func.count(IntakeSession.id)).where(IntakeSession.status == "reviewed")
    )
    reviewed_count = rev_res.scalar() or 0

    # Language breakdown
    lang_res = await db.execute(
        select(IntakeSession.preferred_language, func.count(IntakeSession.id))
        .group_by(IntakeSession.preferred_language)
    )
    languages_breakdown = {row[0]: row[1] for row in lang_res.all()}

    return DashboardStatsResponse(
        total_intakes_today=total_count,
        active_in_queue=active_count,
        critical_red_flags=red_flags_count,
        urgent_triages=urg_count,
        routine_triages=routine_count,
        reviewed_count=reviewed_count,
        average_wait_minutes=12,
        languages_breakdown=languages_breakdown
    )

@router.get("/queue", response_model=List[QueueItemResponse])
async def get_intake_queue(
    triage_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(IntakeSession).order_by(
        IntakeSession.has_red_flags.desc(),
        IntakeSession.triage_score.asc(),
        IntakeSession.created_at.asc()
    )

    if triage_level and triage_level != "ALL":
        query = query.where(IntakeSession.triage_level == triage_level)
    
    if status and status != "ALL":
        query = query.where(IntakeSession.status == status)

    if language and language != "ALL":
        query = query.where(IntakeSession.preferred_language == language)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (IntakeSession.patient_name.ilike(search_pattern)) |
            (IntakeSession.chief_complaint.ilike(search_pattern))
        )

    result = await db.execute(query)
    sessions = result.scalars().all()

    queue_items = []
    now = datetime.utcnow()
    for s in sessions:
        wait_minutes = int((now - s.created_at).total_seconds() / 60)
        queue_items.append(
            QueueItemResponse(
                session_id=s.session_id,
                patient_name=s.patient_name,
                patient_age=s.patient_age,
                patient_gender=s.patient_gender,
                preferred_language=s.preferred_language,
                status=s.status,
                triage_level=s.triage_level,
                triage_score=s.triage_score,
                has_red_flags=s.has_red_flags,
                chief_complaint=s.chief_complaint,
                red_flags_count=1 if s.has_red_flags else 0,
                wait_time_minutes=max(1, wait_minutes),
                created_at=s.created_at
            )
        )

    return queue_items

@router.get("/patient/{session_id}", response_model=PatientDetailResponse)
async def get_patient_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Session
    sess_res = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    # Messages
    msgs_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msgs_res.scalars().all()

    # Clinical Summary
    sum_res = await db.execute(select(ClinicalSummary).where(ClinicalSummary.session_id == session_id))
    summary = sum_res.scalars().first()

    summary_resp = None
    if summary:
        red_flags_json = []
        try:
            red_flags_json = json.loads(summary.red_flags_detected) if summary.red_flags_detected else []
        except Exception:
            pass

        meds = []
        try:
            meds = json.loads(summary.current_medications) if summary.current_medications else []
        except Exception:
            meds = summary.current_medications

        allergies = []
        try:
            allergies = json.loads(summary.allergies) if summary.allergies else []
        except Exception:
            allergies = summary.allergies

        ros = {}
        try:
            ros = json.loads(summary.review_of_systems) if summary.review_of_systems else {}
        except Exception:
            ros = summary.review_of_systems

        summary_resp = ClinicalSummaryResponse(
            id=summary.id,
            session_id=summary.session_id,
            patient_id=summary.patient_id,
            chief_complaint=summary.chief_complaint,
            hpi=summary.hpi,
            onset=summary.onset,
            severity_scale=summary.severity_scale,
            current_medications=meds,
            allergies=allergies,
            review_of_systems=ros,
            red_flags_detected=red_flags_json,
            triage_rationale=summary.triage_rationale,
            soap_subjective=summary.soap_subjective,
            soap_objective=summary.soap_objective,
            soap_assessment=summary.soap_assessment,
            soap_plan=summary.soap_plan,
            clinician_notes=summary.clinician_notes,
            reviewed_by=summary.reviewed_by,
            reviewed_at=summary.reviewed_at,
            created_at=summary.created_at,
            updated_at=summary.updated_at
        )

    # Record HIPAA Audit Log
    audit = AuditLog(
        action="VIEW_PATIENT_INTAKE",
        resource_type="intake_session",
        resource_id=session_id,
        details=f"Clinician accessed intake record for patient {session.patient_name}."
    )
    db.add(audit)
    await db.commit()

    return PatientDetailResponse(
        intake_session=IntakeSessionResponse.model_validate(session),
        messages=[ChatMessageItem.model_validate(m) for m in messages],
        clinical_summary=summary_resp
    )

@router.put("/intake/{session_id}/soap")
async def update_soap_notes(
    session_id: str,
    payload: UpdateSoapRequest,
    db: AsyncSession = Depends(get_db)
):
    sum_res = await db.execute(select(ClinicalSummary).where(ClinicalSummary.session_id == session_id))
    summary = sum_res.scalars().first()
    if not summary:
        raise HTTPException(status_code=404, detail="Clinical summary not found")

    sess_res = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = sess_res.scalars().first()

    if payload.soap_subjective is not None:
        summary.soap_subjective = payload.soap_subjective
    if payload.soap_objective is not None:
        summary.soap_objective = payload.soap_objective
    if payload.soap_assessment is not None:
        summary.soap_assessment = payload.soap_assessment
    if payload.soap_plan is not None:
        summary.soap_plan = payload.soap_plan
    if payload.clinician_notes is not None:
        summary.clinician_notes = payload.clinician_notes

    summary.reviewed_at = datetime.utcnow()
    summary.updated_at = datetime.utcnow()

    if session:
        session.status = payload.status or "reviewed"
        session.updated_at = datetime.utcnow()

    # Log audit trail
    audit = AuditLog(
        action="UPDATE_SOAP_NOTE",
        resource_type="clinical_summary",
        resource_id=session_id,
        details="Clinician updated and approved SOAP note documentation."
    )
    db.add(audit)
    await db.commit()

    return {"message": "SOAP note updated successfully", "status": session.status if session else "reviewed"}

@router.put("/intake/{session_id}/triage")
async def update_triage_level(
    session_id: str,
    payload: UpdateTriageRequest,
    db: AsyncSession = Depends(get_db)
):
    sess_res = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    session.triage_level = payload.triage_level
    session.triage_score = payload.triage_score
    session.updated_at = datetime.utcnow()

    audit = AuditLog(
        action="MANUAL_TRIAGE_OVERRIDE",
        resource_type="intake_session",
        resource_id=session_id,
        details=f"Triage updated to {payload.triage_level} (Score {payload.triage_score}). Rationale: {payload.rationale or 'Clinician judgment'}."
    )
    db.add(audit)
    await db.commit()

    return {"message": "Triage updated successfully", "triage_level": session.triage_level, "triage_score": session.triage_score}

