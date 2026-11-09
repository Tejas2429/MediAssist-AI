# MediAssist AI 🏥
> **Multilingual Patient Intake Companion & Clinical Workflow Triage Platform**  
> *Built with FastAPI, React (TypeScript + Vite + Tailwind CSS), PostgreSQL/SQLite Dual-Engine, and Google Gemini AI.*

---

## 🌟 Executive Overview

**MediAssist AI** modernizes front-door hospital and outpatient intake by eliminating language barriers, automating structured data collection, and safeguarding patients through real-time clinical red-flag triage.

- **Multilingual Patient Intake**: Seamless conversational intake in Spanish, Hindi, French, Mandarin, Arabic, German, and English with live Speech-to-Text and Text-to-Speech support.
- **Dual-Layer Red-Flag Detection**: Instant identification of critical life-threatening emergencies (e.g. STEMI/Acute Coronary Syndrome, Stroke FAST criteria, Severe Respiratory Distress, Anaphylaxis, Sepsis) triggering emergency staff alerts within seconds.
- **Automated Clinical SOAP Note Generation**: Powered by Google Gemini AI to synthesize unstructured patient interactions into standardized Subjective, Objective, Assessment, and Plan (SOAP) clinical documentation.
- **Clinician Triage Station & EHR Workflows**: Live queue with Emergency Severity Index (ESI 1–5) triaging, color-coded urgency banners, language distribution analytics, and HIPAA-compliant audit logging.

---

## 🏗️ System Architecture

```
                                      ┌─────────────────────────────────────┐
                                      │        Patient Kiosk / Mobile       │
                                      │  (Multilingual Voice / Text Chat)   │
                                      └──────────────────┬──────────────────┘
                                                         │
                                               HTTPS REST / JSON
                                                         │
                                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Backend Core                                  │
│                                                                                        │
│  ┌────────────────────────┐   ┌───────────────────────────┐   ┌─────────────────────┐  │
│  │   PHI Redaction &      │   │   Deterministic Red-Flag  │   │  Google Gemini AI   │  │
│  │   De-identification    ├──►│       Triage Engine       ├──►│  Multilingual Engine│  │
│  └────────────────────────┘   └─────────────┬─────────────┘   └──────────┬──────────┘  │
│                                             │                            │             │
│                                             ▼                            ▼             │
│                              ┌─────────────────────────────┐   ┌────────────────────┐  │
│                              │  Emergency Alert Broadcast  │   │ SOAP Note Generator│  │
│                              └─────────────────────────────┘   └────────────────────┘  │
│                                                                                        │
│                                ┌─────────────────────────┐                             │
│                                │ SQLAlchemy Async ORM    │                             │
│                                └────────────┬────────────┘                             │
└─────────────────────────────────────────────┼──────────────────────────────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │       PostgreSQL        │                     │     SQLite Fallback     │
         │   (Production / Docker) │                     │    (Zero-Setup Local)   │
         └─────────────────────────┘                     └─────────────────────────┘
                      ▲
                      │
        ┌─────────────┴─────────────┐
        │   Clinician Workstation   │
        │  (Real-Time Triage Queue, │
        │   SOAP Review & Sign-Off) │
        └───────────────────────────┘
```

---

## 🚀 Key Modules & Capabilities

### 1. Multilingual Patient Intake Companion
- **Languages Supported**: Spanish (Español), Hindi (हिन्दी), French (Français), Mandarin (中文), Arabic (العربية), German (Deutsch), and English.
- **Voice-Enabled Interface**: Integrates browser Web Speech API for voice dictation and native audio speech synthesis read-aloud.
- **Clinical OPQRST Progression**: Naturally walks patients through symptom Onset, Provocation, Quality, Radiation, Severity (1–10 scale), Time/duration, and medical/allergy history.
- **Rapid Tap Chips**: Suggested follow-up prompt chips allow one-touch mobile or kiosk answering.

### 2. Dual-Layer Red-Flag Detection & ESI Triaging
Combines deterministic regex heuristics across multiple languages with Gemini safety validation:
- **Acute Coronary Syndrome (ACS / MI)**: Crushing substernal chest pressure, left arm/jaw radiation, diaphoresis.
- **Acute Stroke (FAST Signs)**: Unilateral facial droop, arm weakness, slurred speech / acute aphasia.
- **Severe Respiratory Distress**: Hypoxia, stridor, acute severe bronchospasm unresponsive to rescue inhalers.
- **Anaphylaxis**: Throat constriction, tongue swelling, acute severe urticaria with dyspnea.
- **Severe Sepsis & Meningitis**: Fever over 104°F with altered mental status, neck stiffness with photophobia.

### 3. Clinician Triage Dashboard
- **Urgent Red-Flag Alerts**: Prominent flashing banners alert clinical teams immediately when an emergency case enters the intake queue.
- **Interactive Patient Queue**: Filterable by triage category (`EMERGENCY`, `URGENT`, `ROUTINE`), status (`escalated`, `submitted`, `reviewed`), language, and name search.
- **Side-by-Side Multilingual Review**: View original patient dialogues side-by-side with instant clinical English translations.
- **Standardized SOAP Note Editor**: Editable Subjective, Objective, Assessment, Plan with physician addenda, one-click sign-off, and EHR print export.

### 4. Security & HIPAA Safeguards
- **Protected Health Information (PHI) Redaction**: Automated sanitization regex strips SSNs, phone numbers, emails, and credit cards before prompt transmission to LLMs.
- **Role-Based Access Control (RBAC)**: JWT authentication securing clinician routes.
- **Audit Trails**: `audit_logs` table records every intake lookup, triage override, and SOAP note update.

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Run the Backend (FastAPI)
```powershell
# From root directory:
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API will run at `http://localhost:8000`. Interactive Swagger docs available at `http://localhost:8000/docs`.*

### 2. Run the Frontend (React + Vite)
```powershell
# In a new terminal:
cd frontend
npm run dev
```
*Frontend will open at `http://localhost:5173`.*

### 3. Pre-Seeded Demo Cases
The database comes pre-seeded with realistic cases:
- 🇪🇸 **Maria Elena Rodriguez (58yo)**: Acute Coronary Syndrome (Chest pressure radiating to left arm) — **EMERGENCY (ESI 1)**.
- 🇮🇳 **Rajesh Sharma (42yo)**: Acute severe asthma attack unresponsive to inhaler in Hindi — **URGENT (ESI 2)**.
- 🇫🇷 **Jean-Luc Moreau (62yo)**: Stroke FAST symptoms in French — **EMERGENCY (ESI 1)**.
- 🇺🇸 **Sarah Jenkins (29yo)**: Ankle sprain routine consultation — **ROUTINE (ESI 4)**.
- 🇨🇳 **Wei Zhang (36yo)**: Migraine evaluation in Mandarin — **ROUTINE (ESI 4)**.

**Demo Clinician Credentials:**
- **Email**: `doctor@mediassist.ai`
- **Password**: `doctor123`

---

## 🧪 Testing Google Gemini AI Integration
To connect directly to Google's live Gemini API:
```powershell
$env:GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY"
```
*Note: If no API key is provided, MediAssist AI seamlessly falls back to its built-in clinical intelligence engine, ensuring complete standalone execution anytime!*

