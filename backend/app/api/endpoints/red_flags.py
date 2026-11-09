from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.intake_session import IntakeSession
from app.models.clinical_summary import ClinicalSummary
from app.models.audit_log import AuditLog
from app.schemas.intake import RedFlagAlert
from app.services.triage_engine import scan_text_for_red_flags
import json

router = APIRouter()

@router.get("/active")
async def get_active_red_flags(db: AsyncSession = Depends(get_db)):
    """
    Returns high-priority feed of all patients with active Red Flags or Emergency Triage.
    """
    query = (
        select(IntakeSession)
        .where((IntakeSession.has_red_flags == True) | (IntakeSession.triage_level == "EMERGENCY"))
        .order_by(desc(IntakeSession.created_at))
        .limit(20)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    alerts = []
    for s in sessions:
        # Fetch summary if available
        sum_res = await db.execute(select(ClinicalSummary).where(ClinicalSummary.session_id == s.session_id))
        summary = sum_res.scalars().first()
        
        flags = []
        if summary and summary.red_flags_detected:
            try:
                flags = json.loads(summary.red_flags_detected)
            except Exception:
                flags = []
        
        # If no summary flags stored yet, re-scan chief complaint
        if not flags and s.chief_complaint:
            flags = scan_text_for_red_flags(s.chief_complaint)

        alerts.append({
            "session_id": s.session_id,
            "patient_name": s.patient_name,
            "patient_age": s.patient_age,
            "patient_gender": s.patient_gender,
            "language": s.preferred_language,
            "chief_complaint": s.chief_complaint,
            "triage_level": s.triage_level,
            "triage_score": s.triage_score,
            "status": s.status,
            "red_flags": flags,
            "created_at": s.created_at
        })

    return alerts

@router.post("/acknowledge/{session_id}")
async def acknowledge_red_flag(session_id: str, db: AsyncSession = Depends(get_db)):
    sess_res = await db.execute(select(IntakeSession).where(IntakeSession.session_id == session_id))
    session = sess_res.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    audit = AuditLog(
        action="ACKNOWLEDGE_RED_FLAG",
        resource_type="intake_session",
        resource_id=session_id,
        details=f"Emergency red-flag alert acknowledged for patient {session.patient_name}."
    )
    db.add(audit)
    await db.commit()

    return {"message": "Red flag alert acknowledged", "session_id": session_id}

