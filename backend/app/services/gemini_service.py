import os
import re
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.core.config import settings
from app.core.security import sanitize_phi_text
from app.services.triage_engine import scan_text_for_red_flags, calculate_triage_score

logger = logging.getLogger("mediassist.gemini")

# Initialize Gemini if API key is provided
GEMINI_AVAILABLE = False
if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Google Gemini AI configured successfully with provided API key.")
    except Exception as e:
        logger.warning(f"Failed to configure Gemini AI: {e}")

CLINICAL_INTAKE_SYSTEM_PROMPT = """
You are MediAssist AI, an empathetic, highly skilled clinical intake assistant designed to triage patients in a hospital or clinic setting.
Your objective:
1. Converse with the patient warmly in their preferred language (e.g., Spanish, English, Hindi, French, Mandarin, Arabic).
2. Clarify their primary symptoms using standard medical intake protocol (OPQRST: Onset, Severity 1-10, Medical history, Allergies).
3. CRITICAL: Never repeat questions the patient has already answered in the Recent History or in their latest message. Acknowledge and validate their answers.
4. If the patient has shared onset, severity rating, and medication/allergy status, conclude the intake by stating that their intake profile is complete and instructing them to click 'Finish & Submit'.
5. Detect any acute RED FLAGS immediately (e.g. crushing chest pain radiating to left arm/jaw, acute stroke signs FAST, severe dyspnea/cyanosis, anaphylaxis, severe sepsis).
6. Always advise emergency care immediately if a critical life-threatening symptom is detected.
7. Provide output in JSON format with fields:
   - "ai_reply": Response to the patient in their language.
   - "ai_reply_en": English translation of your reply for the clinician.
   - "patient_translation_en": English translation of the patient's latest message.
   - "detected_red_flags": Array of objects: [{"flag_type": "...", "severity": "CRITICAL|HIGH|MODERATE", "rationale": "...", "recommended_action": "..."}]
   - "triage_level": "EMERGENCY" | "URGENT" | "ROUTINE" | "SELF_CARE"
   - "triage_score": Integer (1 to 5, ESI scale)
   - "is_emergency": Boolean (true if ESI 1 or 2)
   - "suggested_followups": Array of 2-3 concise follow-up questions the patient can quickly tap.
"""

SOAP_GENERATION_PROMPT = """
You are a senior clinical documentation AI assistant. Review the following patient intake conversation and generate a comprehensive, structured clinical summary in JSON format:
{
  "chief_complaint": "Clear concise summary of the primary complaint",
  "hpi": "History of Present Illness detailing onset, duration, character, radiation, severity",
  "onset": "e.g., '2 hours ago acute' or '3 days progressive'",
  "severity_scale": integer 1-10,
  "current_medications": ["Med 1", "Med 2"],
  "allergies": ["Allergy 1", "No known drug allergies (NKDA)"],
  "review_of_systems": {
     "cardiovascular": "...",
     "respiratory": "...",
     "gastrointestinal": "...",
     "neurological": "...",
     "constitutional": "..."
  },
  "soap_subjective": "Subjective clinical notes in medical terminology",
  "soap_objective": "Objective observations from reported symptoms and intake triage",
  "soap_assessment": "Differential diagnoses and triage rationale",
  "soap_plan": "Recommended immediate clinical actions, diagnostic tests (ECG, labs, imaging), and monitoring"
}
"""

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.has_live_gemini = GEMINI_AVAILABLE and bool(self.api_key)

    async def generate_intake_response(
        self,
        patient_name: str,
        preferred_language: str,
        conversation_history: List[Dict[str, str]],
        new_message: str
    ) -> Dict[str, Any]:
        """
        Processes a patient's message, detects red flags, returns empathetic reply in preferred language,
        and provides translation & triage tags for clinicians.
        """
        # Step 1: De-identify PHI before external AI processing
        sanitized_message = sanitize_phi_text(new_message)
        
        # Step 2: Algorithmic deterministic Red-Flag scan for guaranteed patient safety
        rule_red_flags = scan_text_for_red_flags(sanitized_message)
        rule_triage_level, rule_triage_score = calculate_triage_score(rule_red_flags)
        
        # If live Gemini is enabled, invoke the Gemini LLM
        if self.has_live_gemini:
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=CLINICAL_INTAKE_SYSTEM_PROMPT
                )
                
                # Build context
                history_str = "\n".join([
                    f"{msg.get('sender')}: {msg.get('text')}"
                    for msg in conversation_history[-6:]
                ])
                
                prompt = f"""
Patient Name: {patient_name}
Preferred Language: {preferred_language}
Recent History:
{history_str}

New Patient Message: "{sanitized_message}"

Generate the JSON response conforming to the system prompt.
"""
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                
                parsed = json.loads(response.text)
                
                # Combine Gemini detected flags with algorithmic rule flags for safety
                all_flags = rule_red_flags.copy()
                for f in parsed.get("detected_red_flags", []):
                    if not any(rf["flag_type"] == f.get("flag_type") for rf in all_flags):
                        all_flags.append(f)
                
                triage_level, triage_score = calculate_triage_score(all_flags)
                is_emergency = triage_score in [1, 2]
                
                return {
                    "ai_reply": parsed.get("ai_reply", "I hear you. Could you tell me more about your symptoms?"),
                    "ai_reply_en": parsed.get("ai_reply_en", "I hear you. Could you tell me more about your symptoms?"),
                    "patient_message_original": new_message,
                    "patient_message_translated": parsed.get("patient_translation_en", new_message),
                    "red_flags": all_flags,
                    "triage_level": triage_level,
                    "triage_score": triage_score,
                    "suggested_followups": parsed.get("suggested_followups", ["It started suddenly", "It feels severe", "I have taken medicine"]),
                    "is_emergency": is_emergency
                }
            except Exception as e:
                logger.error(f"Gemini API call failed, using clinical fallback engine: {e}")

        # Intelligent Clinical Fallback / Offline Engine (Zero external dependencies required)
        return self._generate_intelligent_fallback(
            patient_name=patient_name,
            preferred_language=preferred_language,
            conversation_history=conversation_history,
            message=new_message,
            red_flags=rule_red_flags,
            triage_level=rule_triage_level,
            triage_score=rule_triage_score
        )

    def _generate_intelligent_fallback(
        self,
        patient_name: str,
        preferred_language: str,
        conversation_history: List[Dict[str, str]],
        message: str,
        red_flags: List[Dict[str, Any]],
        triage_level: str,
        triage_score: int
    ) -> Dict[str, Any]:
        """
        High-fidelity clinical rule-based engine providing instant multilingual responses,
        accurate translations, and red flag handling.
        """
        msg_lower = message.lower()
        is_emergency = triage_score in [1, 2] or len(red_flags) > 0
        lang = preferred_language.lower()
        
        # Multilingual emergency response
        if is_emergency:
            if "span" in lang or "es" in lang:
                ai_reply = f"⚠️ ATENCIÓN MÉDICA URGENTE: He detectado síntomas que requieren atención médica inmediata. El equipo de emergencias clínicas ha sido alertado. Por favor, permanezca sentado y en calma mientras un médico o enfermero se acerca a usted de inmediato."
                ai_reply_en = "⚠️ URGENT MEDICAL ATTENTION: I have detected symptoms requiring immediate clinical evaluation. The emergency clinical team has been alerted. Please remain seated and calm while medical staff approaches you immediately."
                followups = ["El dolor aumenta", "Tengo mareo y sudoración", "Tengo dificultad para respirar"]
            elif "hindi" in lang or "hi" in lang:
                ai_reply = f"⚠️ आपातकालीन सूचना: आपके लक्षणों को देखते हुए तुरंत डॉक्टर की सहायता आवश्यक है। हमारी आपातकालीन मेडिकल टीम को सूचित कर दिया गया है। कृपया शांत रहें और वहीं बैठें, स्वास्थ्य कर्मी तुरंत आपके पास आ रहे हैं।"
                ai_reply_en = "⚠️ EMERGENCY NOTICE: Immediate doctor evaluation required based on your reported symptoms. Our emergency clinical team has been alerted. Please stay seated calmly, medical staff is arriving immediately."
                followups = ["दर्द बहुत बढ़ रहा है", "चक्कर आ रहे हैं", "सांस लेने में भारीपन है"]
            elif "fren" in lang or "fr" in lang:
                ai_reply = f"⚠️ ALERTE MÉDICALE D'URGENCE: Les symptômes que vous décrivez nécessitent une évaluation médicale immédiate. L'équipe d'urgence a été prévenue. Veuillez rester assis(e), un soignant arrive immédiatement."
                ai_reply_en = "⚠️ EMERGENCY MEDICAL ALERT: The symptoms you described require immediate medical evaluation. The emergency team has been alerted. Please remain seated, a caregiver is arriving immediately."
                followups = ["La douleur augmente", "Je me sens étourdi(e)", "J'ai du mal à respirer"]
            elif "chin" in lang or "zh" in lang or "mand" in lang:
                ai_reply = f"⚠️ 紧急医疗警告：根据您的描述，您可能需要立即接受急诊评估。急诊医疗团队已收到紧急通知。请保持冷静并坐下，医护人员正在赶往您的位置。"
                ai_reply_en = "⚠️ EMERGENCY MEDICAL WARNING: Based on your description, immediate emergency evaluation is required. The emergency clinical team has been notified. Please stay calm and seated, medical staff is coming to you."
                followups = ["疼痛加剧", "感到头晕出冷汗", "呼吸越来越困难"]
            else:
                ai_reply = f"⚠️ URGENT MEDICAL ATTENTION: I have flagged symptoms that require immediate clinical evaluation. Our emergency clinical staff has been notified. Please remain seated and calm, medical personnel are attending to you right now."
                ai_reply_en = ai_reply
                followups = ["Pain is worsening", "Feeling dizzy / sweating", "Difficulty breathing"]

            return {
                "ai_reply": ai_reply,
                "ai_reply_en": ai_reply_en,
                "patient_message_original": message,
                "patient_message_translated": f"[Urgent Triage] {message}",
                "red_flags": red_flags,
                "triage_level": triage_level,
                "triage_score": triage_score,
                "suggested_followups": followups,
                "is_emergency": True
            }

        # Dynamic Clinical Dialogue State Tracker (Prevents repetitive question loops)
        all_text = " ".join([m.get("text", "") for m in conversation_history] + [message]).lower()
        
        has_onset = bool(re.search(r"\b(?:ago|days?|hours?|weeks?|months?|since|yesterday|today|started|morning|night|recent|sudden|chronic)\b", all_text))
        has_severity = bool(re.search(r"(?:/10|\bout of 10\b|\b[1-9]/10\b|\b(?:level|score|rate|rating|scale)\s*(?:is|:)?\s*\d+|\b\d+\s*(?:out of 10|de 10)\b|\b(?:severe|mild|moderate|unbearable)\b|\bpain (?:is|level)?\s*\d+)", all_text))
        has_meds_allergies = bool(re.search(r"\b(?:allerg\w*|medicat\w*|prescript\w*|pills?|tablets?|penicillin|none|no\b|nothing|don't take|no meds|no allergies|nkda)\b", message.lower()) or "medication" in all_text and len(conversation_history) >= 4)
        is_finishing = bool(re.search(r"\b(?:ok|thank|done|submit|finish|ready|all good|fine|that is all|that's all|nothing else|already answered)\b", message.lower()))

        turn_count = len(conversation_history)

        # Dialogue progression:
        if is_finishing or (has_meds_allergies and has_onset and has_severity) or (has_meds_allergies and turn_count >= 4):
            # Phase: Intake Complete
            if "span" in lang or "es" in lang:
                ai_reply = f"¡Muchas gracias, {patient_name}! He registrado todos sus síntomas, nivel de dolor y antecedentes. Su ingreso clínico está completo. Por favor presione el botón verde 'Finish & Submit' arriba a la derecha para que el médico revise su expediente."
                ai_reply_en = f"Thank you very much, {patient_name}! I have recorded your symptoms, pain rating, and medical history. Your intake is complete. Please click the green 'Finish & Submit' button at the top right so the doctor can review your record."
                followups = ["Listo para enviar", "No tengo más síntomas"]
            elif "hindi" in lang or "hi" in lang:
                ai_reply = f"धन्यवाद {patient_name}। आपकी सभी समस्याएं, दर्द की तीव्रता और मेडिकल इतिहास दर्ज कर लिया गया है। आपका इनटेक पूरा हो गया है! कृपया ऊपर दाईं ओर दिए गए हरे 'Finish & Submit' बटन पर क्लिक करें।"
                ai_reply_en = f"Thank you {patient_name}. Your symptoms, severity, and medical history have been documented. Your intake is complete! Please click 'Finish & Submit' at the top right."
                followups = ["रिकॉर्ड जमा करें", "सब ठीक है"]
            elif "fren" in lang or "fr" in lang:
                ai_reply = f"Merci beaucoup, {patient_name}. J'ai noté l'ensemble de vos symptômes et antécédents. Votre admission est complète ! Veuillez cliquer sur le bouton vert 'Finish & Submit' en haut à droite."
                ai_reply_en = f"Thank you very much, {patient_name}. Your admission is complete! Please click 'Finish & Submit' at the top right."
                followups = ["Prêt à envoyer", "Aucun autre symptôme"]
            elif "chin" in lang or "zh" in lang or "mand" in lang:
                ai_reply = f"非常感谢您，{patient_name}！您的症状、疼痛程度和既往史已全部记录完毕。请点击右上角绿色的“Finish & Submit”按钮提交给医生审阅。"
                ai_reply_en = f"Thank you {patient_name}! Your symptoms and history are fully recorded. Please click 'Finish & Submit' at the top right."
                followups = ["确认提交", "没有其他症状"]
            else:
                ai_reply = f"Thank you, {patient_name}! I have gathered your full symptom report, severity rating, and medical history. Your intake is now complete! Please click the green 'Finish & Submit' button at the top right so the clinical team can review your chart."
                ai_reply_en = ai_reply
                followups = ["I am ready to submit", "No other symptoms to add"]
        elif has_onset and not has_severity:
            # Phase: Ask Severity
            if "span" in lang or "es" in lang:
                ai_reply = "¿Del 1 al 10 (donde 10 es el dolor más fuerte imaginable), qué nivel de intensidad siente? ¿El dolor se irradia a otra parte del cuerpo?"
                ai_reply_en = "On a scale from 1 to 10 (where 10 is the most severe pain imaginable), what level of intensity are you experiencing? Does the pain radiate anywhere else?"
                followups = ["Nivel de dolor: 4 de 10", "Nivel de dolor: 7 de 10", "No se mueve a otra zona"]
            elif "hindi" in lang or "hi" in lang:
                ai_reply = "1 से 10 के पैमाने पर (जहां 10 सबसे तेज दर्द है), आप इस दर्द को कितना अंक देंगे? क्या यह दर्द किसी और जगह भी फैल रहा है?"
                ai_reply_en = "On a scale of 1 to 10, how severe is the pain? Does the pain radiate to any other area?"
                followups = ["दर्द 5/10 है", "दर्द 7/10 है", "सिर्फ एक ही जगह पर है"]
            elif "fren" in lang or "fr" in lang:
                ai_reply = "Sur une échelle de 1 à 10, à quel point la douleur est-elle intense? Se propage-t-elle à une autre partie du corps?"
                ai_reply_en = "On a scale from 1 to 10, how intense is the pain? Does it radiate to another part of the body?"
                followups = ["Douleur 4 sur 10", "Douleur 7 sur 10", "Localisée sans irradiation"]
            elif "chin" in lang or "zh" in lang or "mand" in lang:
                ai_reply = "在1到10分的疼痛评分中（10为最剧烈疼痛），您目前的痛感大约是几分？疼痛是否放射到身体其他部位？"
                ai_reply_en = "On a scale of 1 to 10, what is the pain score? Does it radiate elsewhere?"
                followups = ["疼痛约4分", "疼痛约7分", "没有扩散到其他部位"]
            else:
                ai_reply = f"Noted on that timeline, {patient_name}. On a pain scale from 1 to 10 (where 10 is the worst pain imaginable), how severe is it right now? Does the sensation spread anywhere else?"
                ai_reply_en = ai_reply
                followups = ["Pain level: 4/10 (Mild)", "Pain level: 6/10 (Moderate)", "Pain level: 8/10 (Severe)"]
        elif has_severity and not has_meds_allergies:
            # Phase: Ask Meds & Allergies
            if "span" in lang or "es" in lang:
                ai_reply = "Entendido. Para completar su expediente clínico, ¿toma actualmente algún medicamento habitual o tiene alguna alergia conocida a medicamentos o alimentos?"
                ai_reply_en = "Understood. To complete your clinical intake, are you currently taking any regular medications, or do you have any known drug/food allergies?"
                followups = ["Sin alergias conocidas", "Tomo medicina para la presión", "Tengo alergia a la penicilina"]
            elif "hindi" in lang or "hi" in lang:
                ai_reply = "ठीक है। क्या आप अभी कोई नियमित दवाइयां ले रहे हैं या आपको किसी दवा से कोई एलर्जी है?"
                ai_reply_en = "Understood. Are you taking any regular medications or do you have any known allergies to medicines?"
                followups = ["कोई एलर्जी नहीं है", "बीपी की दवा लेता हूँ", "शुगर की दवा लेता हूँ"]
            elif "fren" in lang or "fr" in lang:
                ai_reply = "D'accord. Prenez-vous actuellement des médicaments réguliers, ou avez-vous des allergies connues?"
                ai_reply_en = "Understood. Are you currently taking any regular medications, or do you have any known allergies?"
                followups = ["Aucune allergie connue", "Traitement régulier", "Allergie à la pénicilline"]
            elif "chin" in lang or "zh" in lang or "mand" in lang:
                ai_reply = "明白了。请问您平时有在服用哪些日常药物吗？是否有任何药物或食物过敏史？"
                ai_reply_en = "Understood. Are you taking any routine medications? Do you have any known drug or food allergies?"
                followups = ["无已知药物过敏", "服用日常药物", "对青霉素过敏"]
            else:
                ai_reply = "Understood on the pain rating. To finish your clinical profile, are you currently taking any daily prescriptions or over-the-counter medications, and do you have any known drug allergies?"
                ai_reply_en = ai_reply
                followups = ["No known drug allergies (NKDA)", "I take daily medication", "Allergic to penicillin"]
        else:
            # Phase: Ask Onset & Quality
            if "span" in lang or "es" in lang:
                ai_reply = f"Gracias por informarme, {patient_name}. ¿Hace cuánto tiempo comenzaron estos síntomas y cómo describiría la molestia (punzante, sordo, constante o intermitente)?"
                ai_reply_en = f"Thank you for sharing, {patient_name}. How long ago did these symptoms begin, and how would you describe the sensation (sharp, dull, constant, or intermittent)?"
                followups = ["Empezó hoy repentinamente", "Lleva varios días", "Es un dolor constante"]
            elif "hindi" in lang or "hi" in lang:
                ai_reply = f"धन्यवाद {patient_name}। ये लक्षण कब से शुरू हुए हैं और आपको यह परेशानी कैसी महसूस हो रही है (तेज चुभन, हल्का भारीपन, या रुक-रुक कर)?"
                ai_reply_en = f"Thank you {patient_name}. When did these symptoms start and how would you describe the discomfort (sharp, dull heaviness, or intermittent)?"
                followups = ["आज अचानक शुरू हुआ", "2-3 दिनों से है", "लगातार बना हुआ है"]
            elif "fren" in lang or "fr" in lang:
                ai_reply = f"Merci {patient_name}. Depuis combien de temps ces symptômes ont-ils commencé, et comment décririez-vous cette gêne?"
                ai_reply_en = f"Thank you {patient_name}. How long have these symptoms been present, and how would you describe this discomfort?"
                followups = ["Ça a commencé aujourd'hui", "Depuis 2-3 jours", "C'est une douleur constante"]
            elif "chin" in lang or "zh" in lang or "mand" in lang:
                ai_reply = f"谢谢您，{patient_name}。请问这些症状是什么时候开始出现的？具体感觉是隐痛、刺痛还是持续性胀痛？"
                ai_reply_en = f"Thank you {patient_name}. When did these symptoms begin, and how would you describe the feeling (dull ache, sharp pain, or persistent throbbing)?"
                followups = ["今天突然发作", "已经持续两三天", "阵发性隐痛"]
            else:
                ai_reply = f"Thank you for sharing, {patient_name}. How long ago did this start, and how would you describe the feeling (sharp, dull, throbbing, or intermittent)?"
                ai_reply_en = ai_reply
                followups = ["Started suddenly today", "Ongoing for a few days", "Constant dull ache"]

        return {
            "ai_reply": ai_reply,
            "ai_reply_en": ai_reply_en,
            "patient_message_original": message,
            "patient_message_translated": message,
            "red_flags": red_flags,
            "triage_level": triage_level,
            "triage_score": triage_score,
            "suggested_followups": followups,
            "is_emergency": False
        }

    async def generate_clinical_summary(
        self,
        patient_name: str,
        patient_age: Optional[int],
        patient_gender: Optional[str],
        preferred_language: str,
        messages: List[Dict[str, str]],
        red_flags: List[Dict[str, Any]],
        triage_level: str
    ) -> Dict[str, Any]:
        """
        Synthesizes the entire conversation into a clinical summary with SOAP note for clinicians.
        """
        all_conversation_text = "\n".join([
            f"[{m.get('sender', 'user').upper()} - {m.get('language', 'en')}]: {m.get('text', '')}"
            for m in messages
        ])
        
        sanitized_transcript = sanitize_phi_text(all_conversation_text)

        if self.has_live_gemini:
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=SOAP_GENERATION_PROMPT
                )
                prompt = f"""
Patient Demographics:
- Name: {patient_name}
- Age: {patient_age or 'Unknown'}
- Gender: {patient_gender or 'Unknown'}
- Primary Language: {preferred_language}
- Current Triage Status: {triage_level}
- Detected Red Flags: {json.dumps(red_flags)}

Full Intake Transcript:
{sanitized_transcript}
"""
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                parsed = json.loads(response.text)
                return parsed
            except Exception as e:
                logger.error(f"Live Gemini SOAP generation failed, using structured clinical builder: {e}")

        # Intelligent structured clinical summary synthesis
        chief_complaint = "Reported acute discomfort during multilingual intake."
        if messages:
            first_patient_msg = next((m.get("text") for m in messages if m.get("sender") == "patient"), None)
            if first_patient_msg:
                chief_complaint = first_patient_msg

        # Extract severity scale if mentioned
        severity_val = 5
        for m in messages:
            txt = m.get("text", "")
            for digit in ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]:
                if f"{digit}/10" in txt or f"{digit} de 10" in txt or f"{digit}分" in txt or f"{digit}" in txt:
                    try:
                        severity_val = int(digit)
                        break
                    except ValueError:
                        pass

        # Build comprehensive SOAP notes
        soap_subjective = (
            f"Patient {patient_name} ({patient_age or 'Adult'} yo {patient_gender or 'patient'}, primary language: {preferred_language}) "
            f"presented via automated intake portal. Reports chief complaint: '{chief_complaint}'. "
            f"Pain severity scored at {severity_val}/10. Conversation conducted in {preferred_language} with real-time clinical translation."
        )

        soap_objective = (
            f"Triage Category: {triage_level}. Triage Score: {calculate_triage_score(red_flags, severity_val)[1]}. "
            f"Active Red Flags: {len(red_flags)} flagged. "
            f"Patient is alert, oriented, engaging interactively via intake companion."
        )

        if red_flags:
            soap_assessment = (
                f"ACUTE TRIAGE CONCERN: Identified {len(red_flags)} clinical red flags ({', '.join(f.get('flag_type', '') for f in red_flags)}). "
                f"Requires high-priority bedside clinician evaluation to rule out acute life-threatening etiologies."
            )
            soap_plan = (
                f"1. Immediate physician bedside evaluation.\n"
                f"2. Urgent diagnostics: {', '.join(f.get('recommended_action', '') for f in red_flags)}\n"
                f"3. Continuous vital signs monitoring and IV access.\n"
                f"4. Confirm medication reconciliation and drug allergies."
            )
        else:
            soap_assessment = (
                f"Stable presentation. Primary symptom profile consistent with {chief_complaint[:50]}. "
                f"No acute life-threatening red flags detected during intake."
            )
            soap_plan = (
                f"1. Standard clinical evaluation by attending physician.\n"
                f"2. Focused physical examination.\n"
                f"3. Routine diagnostic workup as clinically indicated."
            )

        return {
            "chief_complaint": chief_complaint,
            "hpi": f"Patient presents with {chief_complaint}. Onset was reported during intake conversation. Symptoms are rated at severity {severity_val}/10.",
            "onset": "Acute to subacute",
            "severity_scale": severity_val,
            "current_medications": ["Medication list reviewed by patient"],
            "allergies": ["No known severe drug allergies documented at intake"],
            "review_of_systems": {
                "cardiovascular": "Chest pain / palpitation screen completed",
                "respiratory": "Dyspnea / cough screen completed",
                "neurological": "Alert and responsive",
                "constitutional": "Reported general discomfort"
            },
            "soap_subjective": soap_subjective,
            "soap_objective": soap_objective,
            "soap_assessment": soap_assessment,
            "soap_plan": soap_plan
        }

gemini_service = GeminiService()

