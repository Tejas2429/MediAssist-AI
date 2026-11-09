import re
from typing import List, Dict, Any, Tuple

# Comprehensive multilingual red flag patterns and clinical triggers
RED_FLAG_PATTERNS = [
    {
        "flag_type": "ACUTE_CORONARY_SYNDROME",
        "severity": "CRITICAL",
        "rationale": "Patient reported crushing chest pain, tightness, or pain radiating to left arm/jaw/neck with associated dyspnea or diaphoresis.",
        "action": "Immediate cardiology triage, stat 12-lead ECG (<10 mins), continuous cardiac telemetry, oxygen, notify attending physician for emergent ACS protocol.",
        "keywords": [
            # English
            r"chest pain", r"chest pressure", r"crushing chest", r"radiat.*left arm", r"heart attack", r"chest tight",
            # Spanish
            r"dolor (?:en el |de )?pecho", r"presi[oó]n en el pecho", r"se me va al brazo izquierdo", r"ataque al coraz[oó]n", r"opresi[oó]n tor[aá]cica",
            # French
            r"douleur thoracique", r"douleur [aà] la poitrine", r"irradie dans le bras gauche", r"crise cardiaque",
            # Hindi (Transliterated & Devanagari)
            r"seene me.*dard", r"chhati me.*dard", r"dil ka daura", r"छाती में दर्द", r"सीने में दर्द", r"दिल का दौरा",
            # Mandarin (Pinyin & Hanzi)
            r"xiong tong", r"胸痛", r"胸口痛", r"心脏病"
        ]
    },
    {
        "flag_type": "ACUTE_STROKE_ALERT",
        "severity": "CRITICAL",
        "rationale": "Positive FAST signs: sudden facial droop, unilateral arm/leg weakness, sudden slurred speech, or acute loss of vision/balance.",
        "action": "Activate Emergency Stroke Protocol (Code Stroke), urgent non-contrast head CT, determine last known normal time.",
        "keywords": [
            # English
            r"slurred speech", r"face droop", r"arm numb", r"weakness on one side", r"stroke", r"can't speak", r"paralyz",
            # Spanish
            r"dificultad para hablar", r"cara ca[ií]da", r"brazo dormido", r"par[aá]lisis", r"derrame cerebral", r"no puedo hablar bien",
            # French
            r"difficult[eé] [aà] parler", r"visage d[eé]form[eé]", r"paralysie", r"avc", r"faiblesse d'un c[oô]t[eé]",
            # Hindi
            r"bolne me.*dikkat", r"lakwa", r"ek taraf kamzori", r"लकवा", r"फालिज", r"बोलने में परेशानी",
            # Mandarin
            r"zhong feng", r"中风", r"偏瘫", r"说话不清", r"嘴角歪斜"
        ]
    },
    {
        "flag_type": "SEVERE_RESPIRATORY_DISTRESS",
        "severity": "CRITICAL",
        "rationale": "Inability to breathe adequately, cyanosis, stridor, acute severe asthma exacerbation, or hypoxia.",
        "action": "Immediate respiratory assessment, pulse oximetry, supplemental high-flow O2, nebulized bronchodilators, evaluate for airway compromise.",
        "keywords": [
            # English
            r"can't breathe", r"cannot breathe", r"shortness of breath", r"gasping", r"blue lips", r"suffocating", r"asthma attack",
            # Spanish
            r"no puedo respirar", r"falta de aire", r"me ahogo", r"labios azules", r"ataque de asma", r"dificultad respiratoria",
            # French
            r"peux pas respirer", r"manque d'air", r"essoufflement s[eé]v[eè]re", r"crise d'asthme",
            # Hindi
            r"saans.*nahi.*aa rahi", r"saans phool", r"dama ka daura", r"सांस नहीं आ रही", r"सांस फूलना",
            # Mandarin
            r"hu xi kun nan", r"呼吸困难", r"喘不过气", r"哮喘发作"
        ]
    },
    {
        "flag_type": "ANAPHYLAXIS_ALERT",
        "severity": "CRITICAL",
        "rationale": "Acute allergic reaction with airway compromise, tongue/throat swelling, or anaphylactic shock.",
        "action": "Immediate physician bedside evaluation for anaphylaxis protocol, airway assessment, prepare Epinephrine per physician order, recumbent positioning.",
        "keywords": [
            # English
            r"throat.*(?:clos|tight|swell)", r"(?:swollen.*tongue|tongue.*swell)", r"allergic reaction", r"anaphyla", r"swelling in throat", r"can't swallow.*allerg",
            # Spanish
            r"(?:se me cierra|cerrando).*garganta", r"lengua.*hinch", r"reacci[oó]n al[eé]rgica", r"anafilaxia",
            # French
            r"gorge qui se serre", r"langue gonfl[eé]e", r"choc anaphylactique",
            # Hindi
            r"gala band", r"jeebh sooj", r"allergy reaction", r"गला घुट रहा", r"जीभ में सूजन",
            # Mandarin
            r"hou long shou suo", r"喉咙肿胀", r"过敏性休克"
        ]
    },
    {
        "flag_type": "SEVERE_SEPSIS_INFECTION",
        "severity": "HIGH",
        "rationale": "Severe infection signs with high fever, altered mental status, severe tachycardia, or extreme lethargy.",
        "action": "Urgent lactate, blood cultures x2 prior to broad-spectrum IV antibiotics, rapid IV crystalloid resuscitation.",
        "keywords": [
            # English
            r"high fever.*confusion", r"severe chills.*shaking", r"sepsis", r"fever over 104", r"delirious",
            # Spanish
            r"fiebre muy alta.*confusi[oó]n", r"sepsis", r"escalofr[ií]os incontrolables", r"delirio",
            # French
            r"fi[eè]vre tr[eè]s [eé]lev[eé]e.*confusion", r"sepsis", r"choc septique",
            # Hindi
            r"tez bukhar.*behosh", r"tez bukhar.*chakkar", r"तेज बुखार",
            # Mandarin
            r"gao shao.*hun mi", r"败血症", r"脓毒症", r"高烧不退"
        ]
    },
    {
        "flag_type": "MENINGITIS_SUSPICION",
        "severity": "HIGH",
        "rationale": "Classic triad of high fever, acute nuchal rigidity (stiff neck), and photophobia/petechial rash.",
        "action": "Immediate droplet isolation, emergent lumbar puncture prep, empiric IV antibiotics/corticosteroids.",
        "keywords": [
            # English
            r"stiff neck.*fever", r"fever.*neck stiff", r"meningitis", r"light hurts eyes.*fever",
            # Spanish
            r"cuello r[ií]gido.*fiebre", r"rigidez de nuca", r"meningitis",
            # French
            r"raideur de la nuque", r"m[eé]ningite",
            # Hindi
            r"gardan akad.*bukhar", r"meningitis", r"गर्दन अकड़ना.*बुखार",
            # Mandarin
            r"bo zi fa ying", r"脑膜炎", r"颈部僵硬"
        ]
    },
    {
        "flag_type": "ACUTE_ABDOMINAL_EMERGENCY",
        "severity": "HIGH",
        "rationale": "Severe acute abdominal pain, board-like rigidity, or gastrointestinal hemorrhage (hematemesis/melena).",
        "action": "Surgical consult, NPO, IV access, abdominal imaging (CT AP), blood type & crossmatch.",
        "keywords": [
            # English
            r"vomiting blood", r"black tarry stool", r"unbearable stomach pain", r"rigid stomach", r"burst appendix",
            # Spanish
            r"vomitando sangre", r"heces negras", r"dolor insoportable de est[oó]mago", r"ap[eé]ndice",
            # French
            r"vomir du sang", r"selles noires", r"douleur abdominale insupportable",
            # Hindi
            r"khoon ki ulti", r"pet me asahaniya dard", r"खून की उल्टी", r"पेट में असहनीय दर्द",
            # Mandarin
            r"ou xue", r"呕血", r"便血", r"剧烈腹痛"
        ]
    }
]

def scan_text_for_red_flags(text: str) -> List[Dict[str, Any]]:
    """
    Scans a given text or dialogue history for clinically significant red flags
    across multiple languages using regex heuristics.
    """
    if not text:
        return []
    
    detected = []
    text_clean = text.lower()
    
    for rule in RED_FLAG_PATTERNS:
        matches = []
        for kw in rule["keywords"]:
            if re.search(kw, text_clean, re.IGNORECASE):
                matches.append(kw)
        
        if matches:
            detected.append({
                "flag_type": rule["flag_type"],
                "severity": rule["severity"],
                "rationale": rule["rationale"],
                "recommended_action": rule["action"]
            })
            
    return detected

def calculate_triage_score(red_flags: List[Dict[str, Any]], reported_severity: int = 5) -> Tuple[str, int]:
    """
    Computes standard Emergency Severity Index (ESI-like) score:
    - ESI 1 / 2: EMERGENCY (Critical red flags like STEMI, stroke, anaphylaxis, severe respiratory failure)
    - ESI 3: URGENT (High red flags or severe pain 8-10 with acute symptoms)
    - ESI 4: ROUTINE (Mild-moderate symptoms, stable)
    - ESI 5: SELF_CARE / NON_URGENT (Prescription refill, mild chronic follow-up)
    """
    if not red_flags:
        if reported_severity >= 8:
            return "URGENT", 3
        elif reported_severity >= 4:
            return "ROUTINE", 4
        else:
            return "ROUTINE", 5

    has_critical = any(f.get("severity") == "CRITICAL" for f in red_flags)
    has_high = any(f.get("severity") == "HIGH" for f in red_flags)

    if has_critical:
        return "EMERGENCY", 1
    elif has_high or reported_severity >= 8:
        return "URGENT", 2
    else:
        return "URGENT", 3

