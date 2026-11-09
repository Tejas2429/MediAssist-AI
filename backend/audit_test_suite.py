import sys
import os
import asyncio
import json
import httpx
from datetime import datetime

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token, sanitize_phi_text
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User
from app.models.patient import Patient
from app.models.intake_session import IntakeSession
from app.models.chat_message import ChatMessage
from app.models.clinical_summary import ClinicalSummary
from app.models.audit_log import AuditLog
from app.services.triage_engine import scan_text_for_red_flags, calculate_triage_score
from app.services.gemini_service import gemini_service

API_BASE = "http://127.0.0.1:8000/api"

results = {}

async def test_backend_auth():
    print("\n--- TEST: Authentication & Password Security ---")
    password = "TestClinicalPassword123!"
    hashed = get_password_hash(password)
    is_valid = verify_password(password, hashed)
    is_invalid = verify_password("WrongPassword!", hashed)
    
    token = create_access_token(subject=1)
    decoded = decode_access_token(token)
    
    from datetime import timedelta
    expired_token = create_access_token(subject=1, expires_delta=timedelta(seconds=-10))
    decoded_expired = decode_access_token(expired_token)
    
    auth_res = {
        "password_hashing": "bcrypt",
        "hash_verification_success": is_valid,
        "hash_rejection_success": not is_invalid,
        "jwt_creation_and_decoding": decoded is not None and decoded.get("sub") == "1",
        "jwt_expiration_handling": decoded_expired is None,
        "hardcoded_secret_key_risk": settings.SECRET_KEY == "mediassist-super-secret-production-grade-key-2026"
    }
    print("Auth Test Results:", json.dumps(auth_res, indent=2))
    results["auth"] = auth_res

async def test_database_persistence():
    print("\n--- TEST: Database Persistence & Models ---")
    async with AsyncSessionLocal() as db:
        # Create a test session
        test_session_id = f"audit-test-{datetime.utcnow().timestamp()}"
        session = IntakeSession(
            session_id=test_session_id,
            patient_name="Audit Test Patient",
            preferred_language="Spanish",
            status="in_progress",
            triage_level="ROUTINE",
            triage_score=4
        )
        db.add(session)
        await db.commit()
        
        # Add message
        msg = ChatMessage(
            session_id=test_session_id,
            sender="patient",
            language="Spanish",
            original_text="Prueba de persistencia",
            translated_text="Persistence test"
        )
        db.add(msg)
        await db.commit()
        
        # Read back in a new query
        from sqlalchemy import select
        res = await db.execute(select(IntakeSession).where(IntakeSession.session_id == test_session_id))
        queried_session = res.scalars().first()
        
        msg_res = await db.execute(select(ChatMessage).where(ChatMessage.session_id == test_session_id))
        queried_msg = msg_res.scalars().first()
        
        db_res = {
            "session_persisted": queried_session is not None,
            "patient_name_match": queried_session.patient_name == "Audit Test Patient" if queried_session else False,
            "message_persisted": queried_msg is not None,
            "message_text_match": queried_msg.original_text == "Prueba de persistencia" if queried_msg else False,
            "database_dialect": engine.dialect.name
        }
        print("Database Persistence Results:", json.dumps(db_res, indent=2))
        results["database"] = db_res

async def test_api_endpoints():
    print("\n--- TEST: REST API Endpoints ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Health
        health_resp = await client.get(f"{API_BASE}/health")
        
        # 2. Login
        login_resp = await client.post(f"{API_BASE}/auth/login", json={
            "email": "doctor@mediassist.ai",
            "password": "doctor123"
        })
        token = login_resp.json().get("access_token") if login_resp.status_code == 200 else None
        
        # 3. Queue endpoint (unauthenticated check)
        queue_unauth = await client.get(f"{API_BASE}/clinician/queue")
        
        # 4. Start intake
        intake_start = await client.post(f"{API_BASE}/intake/start", json={
            "patient_name": "Audit Patient Carlos",
            "preferred_language": "Spanish",
            "patient_age": 55,
            "patient_gender": "Male"
        })
        session_id = intake_start.json().get("session_id") if intake_start.status_code == 200 else None
        
        # 5. Send message
        intake_msg = None
        if session_id:
            intake_msg = await client.post(f"{API_BASE}/intake/{session_id}/message", json={
                "message": "Siento un dolor punzante en el pecho y me falta el aire."
            })
            
        # 6. Complete intake
        intake_comp = None
        if session_id:
            intake_comp = await client.post(f"{API_BASE}/intake/{session_id}/complete")
            
        # 7. Get patient detail
        patient_detail = None
        if session_id:
            patient_detail = await client.get(f"{API_BASE}/clinician/patient/{session_id}")

        api_res = {
            "health_status_code": health_resp.status_code,
            "login_status_code": login_resp.status_code,
            "has_token": token is not None,
            "queue_unauthenticated_status": queue_unauth.status_code,
            "queue_unauthenticated_open": queue_unauth.status_code == 200,
            "intake_start_status": intake_start.status_code,
            "session_id_created": session_id is not None,
            "intake_msg_status": intake_msg.status_code if intake_msg else None,
            "intake_comp_status": intake_comp.status_code if intake_comp else None,
            "patient_detail_status": patient_detail.status_code if patient_detail else None,
            "summary_generated": bool(patient_detail and patient_detail.json().get("clinical_summary"))
        }
        print("API Test Results:", json.dumps(api_res, indent=2))
        results["api"] = api_res

async def test_red_flags():
    print("\n--- TEST: Red Flag Detection Accuracy ---")
    test_cases = [
        # True Positives
        ("I have severe crushing chest pain radiating to left arm", "ACUTE_CORONARY_SYNDROME", "CRITICAL"),
        ("Tengo un dolor muy fuerte en el pecho que se me va al brazo izquierdo", "ACUTE_CORONARY_SYNDROME", "CRITICAL"),
        ("I can't breathe, my lips are blue and gasping for air", "SEVERE_RESPIRATORY_DISTRESS", "CRITICAL"),
        ("saans nahi aa rahi hai aur dama ka daura hai", "SEVERE_RESPIRATORY_DISTRESS", "CRITICAL"),
        ("Sudden slurred speech and weakness on one side of my body", "ACUTE_STROKE_ALERT", "CRITICAL"),
        ("Mi cara esta caida y no puedo hablar bien", "ACUTE_STROKE_ALERT", "CRITICAL"),
        ("My throat is closing up and tongue is swollen after eating peanuts", "ANAPHYLAXIS_ALERT", "CRITICAL"),
        ("Vomiting bright red blood with unbearable stomach pain", "ACUTE_ABDOMINAL_EMERGENCY", "HIGH"),
        # True Negatives / Routine
        ("I have mild knee pain when running for 30 minutes", None, None),
        ("Tengo un dolor leve en el dedo del pie", None, None),
        ("Routine refill for blood pressure medication", None, None)
    ]
    
    rf_eval = []
    for text, expected_flag, expected_sev in test_cases:
        detected = scan_text_for_red_flags(text)
        detected_types = [d["flag_type"] for d in detected]
        detected_sevs = [d["severity"] for d in detected]
        
        matched = (expected_flag in detected_types) if expected_flag else (len(detected) == 0)
        rf_eval.append({
            "input": text,
            "expected_flag": expected_flag,
            "detected_flags": detected_types,
            "correct": matched
        })
        
    accuracy = sum(1 for e in rf_eval if e["correct"]) / len(rf_eval)
    print(f"Red Flag Accuracy: {accuracy*100:.1f}%")
    results["red_flags"] = {
        "accuracy": accuracy,
        "cases_tested": len(test_cases),
        "details": rf_eval
    }

async def test_phi_sanitization():
    print("\n--- TEST: PHI Sanitization & Redaction ---")
    sample_phi = "Patient John Doe, SSN 123-45-6789, Phone (555) 234-5678, Email john.doe@hospital.com, CC 4532-1234-5678-9012"
    sanitized = sanitize_phi_text(sample_phi)
    
    phi_res = {
        "original": sample_phi,
        "sanitized": sanitized,
        "ssn_masked": "123-45-6789" not in sanitized,
        "phone_masked": "(555) 234-5678" not in sanitized,
        "email_masked": "john.doe@hospital.com" not in sanitized,
        "cc_masked": "4532-1234-5678-9012" not in sanitized,
        "patient_name_masked": "John Doe" not in sanitized  # Note: Name is NOT masked by regex!
    }
    print("PHI Sanitization Results:", json.dumps(phi_res, indent=2))
    results["phi"] = phi_res

async def test_gemini_integration():
    print("\n--- TEST: Gemini AI Integration State ---")
    gemini_status = {
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_live_mode": gemini_service.has_live_gemini,
        "gemini_sdk_deprecated_notice": "google.generativeai package has ended support per Google notice"
    }
    
    # Test conversational fallback execution
    fallback_response = gemini_service._generate_intelligent_fallback(
        patient_name="Maria",
        preferred_language="Spanish",
        conversation_history=[],
        message="Tengo dolor de cabeza",
        red_flags=[],
        triage_level="ROUTINE",
        triage_score=4
    )
    
    gemini_status["fallback_operational"] = bool(fallback_response.get("ai_reply"))
    gemini_status["fallback_has_translation"] = bool(fallback_response.get("ai_reply_en"))
    print("Gemini Status:", json.dumps(gemini_status, indent=2))
    results["gemini"] = gemini_status

async def main():
    await test_backend_auth()
    await test_database_persistence()
    await test_api_endpoints()
    await test_red_flags()
    await test_phi_sanitization()
    await test_gemini_integration()
    
    # Save results to file for auditing
    with open("backend/audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nAudit tests completed successfully and written to backend/audit_results.json.")

if __name__ == "__main__":
    asyncio.run(main())
