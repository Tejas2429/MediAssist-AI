import asyncio
import json
import uuid
import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import Patient
from app.models.intake_session import IntakeSession
from app.models.chat_message import ChatMessage
from app.models.clinical_summary import ClinicalSummary

async def seed():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        res = await db.execute(select(User).where(User.email == "doctor@mediassist.ai"))
        if res.scalars().first():
            print("Database already seeded with demo records.")
            return

        print("Seeding demo clinician...")
        clinician = User(
            email="doctor@mediassist.ai",
            hashed_password=get_password_hash("doctor123"),
            full_name="Dr. Elena Vance, MD",
            role="clinician",
            department="Emergency Medicine & Acute Care",
            is_active=True
        )
        db.add(clinician)
        await db.flush()

        now = datetime.utcnow()

        # CASE 1: Spanish Emergency (Acute Coronary Syndrome)
        print("Seeding Case 1: Spanish Emergency Cardiac Alert...")
        session_id_1 = str(uuid.uuid4())
        session_1 = IntakeSession(
            session_id=session_id_1,
            patient_name="Maria Elena Rodriguez",
            patient_age=58,
            patient_gender="Female",
            preferred_language="Spanish",
            status="escalated",
            triage_level="EMERGENCY",
            triage_score=1,
            has_red_flags=True,
            chief_complaint="Tengo un dolor muy fuerte y una presión en el pecho que se me va al brazo izquierdo.",
            intake_source="web_kiosk",
            created_at=now - timedelta(minutes=24),
            updated_at=now - timedelta(minutes=18)
        )
        db.add(session_1)

        msgs_1 = [
            ChatMessage(
                session_id=session_id_1,
                sender="ai_assistant",
                language="Spanish",
                original_text="¡Hola, Maria Elena! Soy su asistente médico virtual MediAssist AI. ¿Cuál es el motivo principal de su consulta el día de hoy?",
                translated_text="Hello, Maria Elena! I am your MediAssist AI clinical companion. What is the main reason for your visit today?",
                created_at=now - timedelta(minutes=24)
            ),
            ChatMessage(
                session_id=session_id_1,
                sender="patient",
                language="Spanish",
                original_text="Tengo un dolor muy fuerte y una presión en el pecho que se me va al brazo izquierdo desde hace una hora.",
                translated_text="I have very severe pain and pressure in my chest that radiates to my left arm since an hour ago.",
                created_at=now - timedelta(minutes=22)
            ),
            ChatMessage(
                session_id=session_id_1,
                sender="ai_assistant",
                language="Spanish",
                original_text="⚠️ ATENCIÓN MÉDICA URGENTE: He detectado síntomas que requieren atención médica inmediata. El equipo de emergencias clínicas ha sido alertado. ¿Siente también sudoración fría, mareos o dificultad para respirar?",
                translated_text="⚠️ URGENT MEDICAL ATTENTION: I have detected symptoms requiring immediate clinical evaluation. The emergency team has been alerted. Are you also experiencing cold sweats, dizziness, or shortness of breath?",
                created_at=now - timedelta(minutes=21)
            ),
            ChatMessage(
                session_id=session_id_1,
                sender="patient",
                language="Spanish",
                original_text="Sí, estoy sudando frío y me falta el aire. El dolor es un 9 de 10.",
                translated_text="Yes, I am breaking into a cold sweat and short of breath. The pain is a 9 out of 10.",
                created_at=now - timedelta(minutes=20)
            ),
            ChatMessage(
                session_id=session_id_1,
                sender="ai_assistant",
                language="Spanish",
                original_text="Por favor permanezca sentada y tranquila. Nuestro equipo médico de urgencias ya se está dirigiendo hacia usted con un electrocardiógrafo.",
                translated_text="Please remain seated and calm. Our emergency medical team is heading directly to you with an ECG machine.",
                created_at=now - timedelta(minutes=19)
            )
        ]
        db.add_all(msgs_1)

        summary_1 = ClinicalSummary(
            session_id=session_id_1,
            chief_complaint="Severe retrosternal chest pressure radiating to left arm with diaphoresis and dyspnea.",
            hpi="58yo female presents with 1 hour of acute-onset crushing substernal chest pressure, radiation to left upper extremity, accompanied by cold diaphoresis and shortness of breath. Pain rated 9/10.",
            onset="1 hour ago, acute onset",
            severity_scale=9,
            current_medications=json.dumps(["Atorvastatin 20mg daily", "Lisinopril 10mg daily"]),
            allergies=json.dumps(["Penicillin (Hives)"]),
            review_of_systems=json.dumps({
                "cardiovascular": "Severe substernal chest pain radiating to left arm",
                "respiratory": "Dyspnea reported",
                "constitutional": "Diaphoresis and lightheadedness"
            }),
            red_flags_detected=json.dumps([{
                "flag_type": "ACUTE_CORONARY_SYNDROME",
                "severity": "CRITICAL",
                "rationale": "Crushing chest pain radiating to left arm with diaphoresis and dyspnea.",
                "recommended_action": "Stat 12-lead ECG (<10 mins), troponin, IV access, telemetry, oxygen, aspirin chewable 324mg."
            }]),
            triage_rationale="High probability acute coronary syndrome / STEMI alert.",
            soap_subjective="Patient Maria Elena Rodriguez (58yo female, Spanish-speaking) reports acute crushing chest pressure radiating to left arm, 9/10 severity, diaphoresis.",
            soap_objective="Triage ESI Level 1 (Resuscitation/Emergent). Diaphoretic, acute distress.",
            soap_assessment="Rule out Acute Myocardial Infarction / Unstable Angina.",
            soap_plan="1. Immediate ECG within 10 min\n2. Dual IV access, cardiac monitoring\n3. Bedside troponin & cardiac panel\n4. Cardiology consult on-call",
            created_at=now - timedelta(minutes=18)
        )
        db.add(summary_1)

        # CASE 2: Hindi Urgent (Respiratory Distress / Asthma)
        print("Seeding Case 2: Hindi Urgent Respiratory...")
        session_id_2 = str(uuid.uuid4())
        session_2 = IntakeSession(
            session_id=session_id_2,
            patient_name="Rajesh Sharma",
            patient_age=42,
            patient_gender="Male",
            preferred_language="Hindi",
            status="submitted",
            triage_level="URGENT",
            triage_score=2,
            has_red_flags=True,
            chief_complaint="मुझे 3 घंटे से सांस लेने में बहुत तकलीफ हो रही है और इनहेलर से भी आराम नहीं मिला।",
            intake_source="mobile_app",
            created_at=now - timedelta(minutes=45),
            updated_at=now - timedelta(minutes=35)
        )
        db.add(session_2)

        msgs_2 = [
            ChatMessage(
                session_id=session_id_2,
                sender="ai_assistant",
                language="Hindi",
                original_text="नमस्ते Rajesh! मैं MediAssist AI हूँ। आज आपकी क्या समस्या या तकलीफ है?",
                translated_text="Hello Rajesh! I am MediAssist AI. What problem or discomfort are you experiencing today?",
                created_at=now - timedelta(minutes=45)
            ),
            ChatMessage(
                session_id=session_id_2,
                sender="patient",
                language="Hindi",
                original_text="मुझे 3 घंटे से सांस लेने में बहुत तकलीफ हो रही है, छाती में जकड़न है और इनहेलर लेने के बाद भी सांस नहीं आ रही।",
                translated_text="I have had great difficulty breathing for 3 hours, chest tightness, and can't catch my breath even after taking my inhaler.",
                created_at=now - timedelta(minutes=42)
            ),
            ChatMessage(
                session_id=session_id_2,
                sender="ai_assistant",
                language="Hindi",
                original_text="⚠️ आपातकालीन सूचना: सांस की गंभीर समस्या के लिए तुरंत डॉक्टर की जरूरत है। क्या आपके होंठ नीले पड़ रहे हैं या बोलने में कठिनाई हो रही है?",
                translated_text="⚠️ EMERGENCY NOTICE: Immediate doctor evaluation required for severe respiratory difficulty. Are your lips turning blue or are you struggling to speak full sentences?",
                created_at=now - timedelta(minutes=40)
            )
        ]
        db.add_all(msgs_2)

        summary_2 = ClinicalSummary(
            session_id=session_id_2,
            chief_complaint="Acute asthma exacerbation unresponsive to albuterol inhaler.",
            hpi="42yo male with known asthma history presenting with 3 hours of acute wheezing and dyspnea refractory to rescue inhaler.",
            onset="3 hours ago",
            severity_scale=8,
            current_medications=json.dumps(["Albuterol MDI prn", "Fluticasone propionate"]),
            allergies=json.dumps(["No Known Drug Allergies (NKDA)"]),
            review_of_systems=json.dumps({"respiratory": "Severe dyspnea, wheezing, chest tightness"}),
            red_flags_detected=json.dumps([{
                "flag_type": "SEVERE_RESPIRATORY_DISTRESS",
                "severity": "CRITICAL",
                "rationale": "Severe bronchospasm unresponsive to beta-agonist rescue therapy.",
                "recommended_action": "Stat nebulized Albuterol/Ipratropium, pulse ox, supplemental O2, systemic corticosteroids."
            }]),
            soap_subjective="Patient Rajesh Sharma reports severe dyspnea and tightness unresponsive to home inhaler. Hindi speaking.",
            soap_objective="ESI Level 2. Tachypnea noted.",
            soap_assessment="Acute severe asthma exacerbation.",
            soap_plan="1. Continuous nebulization\n2. Prednisone 60mg oral / IV Methylprednisolone\n3. Peak flow measurement when stabilized",
            created_at=now - timedelta(minutes=35)
        )
        db.add(summary_2)

        # CASE 3: Routine English (Orthopedic sports injury)
        print("Seeding Case 3: English Routine...")
        session_id_3 = str(uuid.uuid4())
        session_3 = IntakeSession(
            session_id=session_id_3,
            patient_name="Sarah Jenkins",
            patient_age=29,
            patient_gender="Female",
            preferred_language="English",
            status="reviewed",
            triage_level="ROUTINE",
            triage_score=4,
            has_red_flags=False,
            chief_complaint="Twisted right ankle during morning run, mild swelling, can bear weight.",
            intake_source="web_kiosk",
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=1, minutes=20)
        )
        db.add(session_3)

        msgs_3 = [
            ChatMessage(
                session_id=session_id_3,
                sender="ai_assistant",
                language="English",
                original_text="Hello Sarah! I am MediAssist AI, your clinical intake companion. What is the main reason for your visit today?",
                translated_text="Hello Sarah! I am MediAssist AI, your clinical intake companion. What is the main reason for your visit today?",
                created_at=now - timedelta(hours=2)
            ),
            ChatMessage(
                session_id=session_id_3,
                sender="patient",
                language="English",
                original_text="I rolled my right ankle while running on a trail this morning. It is swollen and bruised on the outside, pain is 4/10.",
                translated_text="I rolled my right ankle while running on a trail this morning. It is swollen and bruised on the outside, pain is 4/10.",
                created_at=now - timedelta(hours=1, minutes=50)
            )
        ]
        db.add_all(msgs_3)

        summary_3 = ClinicalSummary(
            session_id=session_id_3,
            chief_complaint="Right lateral ankle inversion sprain.",
            hpi="29yo female presents with right lateral ankle injury 4 hours ago. Able to bear weight.",
            onset="4 hours ago",
            severity_scale=4,
            current_medications=json.dumps(["Oral contraceptive"]),
            allergies=json.dumps(["Sulfa drugs"]),
            review_of_systems=json.dumps({"musculoskeletal": "Right lateral ankle pain and localized edema"}),
            red_flags_detected=json.dumps([]),
            soap_subjective="Sarah reports right lateral ankle sprain after inversion injury on trail.",
            soap_objective="ESI 4. Stable vitals. Localized tenderness over anterior talofibular ligament.",
            soap_assessment="Grade I/II lateral ankle sprain. Ottawa Ankle Rules negative for malleolar tenderness.",
            soap_plan="1. RICE protocol (Rest, Ice, Compression, Elevation)\n2. Ibuprofen 400mg tid with food\n3. Supportive elastic ankle brace",
            clinician_notes="Reviewed and approved. Ankle wrap applied.",
            reviewed_by=clinician.id,
            reviewed_at=now - timedelta(hours=1, minutes=20),
            created_at=now - timedelta(hours=1, minutes=45)
        )
        db.add(summary_3)

        # CASE 4: Mandarin Routine (Migraine follow up)
        print("Seeding Case 4: Mandarin Routine...")
        session_id_4 = str(uuid.uuid4())
        session_4 = IntakeSession(
            session_id=session_id_4,
            patient_name="Wei Zhang",
            patient_age=36,
            patient_gender="Male",
            preferred_language="Mandarin",
            status="submitted",
            triage_level="ROUTINE",
            triage_score=4,
            has_red_flags=False,
            chief_complaint="反复偏头痛发作两周，伴有轻度畏光，需要神经内科评估。",
            intake_source="web_kiosk",
            created_at=now - timedelta(hours=1, minutes=10),
            updated_at=now - timedelta(minutes=50)
        )
        db.add(session_4)

        msgs_4 = [
            ChatMessage(
                session_id=session_id_4,
                sender="ai_assistant",
                language="Mandarin",
                original_text="您好，Wei！我是 MediAssist AI 智能医疗助手。请问您今天感觉哪里不舒服？",
                translated_text="Hello Wei! I am MediAssist AI. What symptoms or discomfort are you experiencing today?",
                created_at=now - timedelta(hours=1, minutes=10)
            ),
            ChatMessage(
                session_id=session_id_4,
                sender="patient",
                language="Mandarin",
                original_text="我右侧太阳穴偏头痛已经持续了两周，隔天发作一次，工作看屏幕时有些怕光，疼痛大约5分。",
                translated_text="I have had right temple migraine headaches for two weeks, recurring every other day, with mild light sensitivity when looking at computer screens. Pain is around 5/10.",
                created_at=now - timedelta(hours=1, minutes=5)
            )
        ]
        db.add_all(msgs_4)

        summary_4 = ClinicalSummary(
            session_id=session_id_4,
            chief_complaint="Episodic right-sided migraine headaches with photophobia for 2 weeks.",
            hpi="36yo male presents with 2-week history of recurrent unilateral throbbing headaches, photophobia, pain 5/10, no neurological deficits.",
            onset="2 weeks, episodic",
            severity_scale=5,
            current_medications=json.dumps(["Acetaminophen 500mg prn"]),
            allergies=json.dumps(["NKDA"]),
            review_of_systems=json.dumps({"neurological": "Unilateral headache, photophobia, no vision changes or weakness"}),
            red_flags_detected=json.dumps([]),
            soap_subjective="Patient Wei Zhang reports recurring right temporal migraine with photophobia.",
            soap_objective="ESI 4. Neurological screen negative for acute FAST or focal deficits.",
            soap_assessment="Common migraine without aura.",
            soap_plan="1. Triptan therapy trial (Sumatriptan 50mg)\n2. Headache diary\n3. Lifestyle ergonomics and sleep hygiene",
            created_at=now - timedelta(minutes=50)
        )
        db.add(summary_4)

        await db.commit()
        print("Database seeded successfully with realistic multilingual clinical intake records!")

if __name__ == "__main__":
    asyncio.run(seed())
