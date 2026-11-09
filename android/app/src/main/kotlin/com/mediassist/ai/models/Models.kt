package com.mediassist.ai.models

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: String, // "patient" or "ai_assistant"
    val originalText: String,
    val translatedText: String? = null,
    val language: String = "English",
    val timestamp: Long = System.currentTimeMillis()
)

data class RedFlagAlert(
    val flagType: String,
    val severity: String, // CRITICAL, HIGH, MODERATE
    val rationale: String,
    val recommendedAction: String
)

data class IntakeSession(
    val sessionId: String,
    val patientName: String,
    val patientAge: Int? = null,
    val patientGender: String? = null,
    val preferredLanguage: String = "English",
    var status: String = "in_progress",
    var triageLevel: String = "ROUTINE",
    var triageScore: Int = 4,
    var hasRedFlags: Boolean = false,
    var chiefComplaint: String? = null
)

data class ClinicalSummary(
    val chiefComplaint: String,
    val hpi: String,
    val onset: String,
    val severityScale: Int,
    val soapSubjective: String,
    val soapObjective: String,
    val soapAssessment: String,
    val soapPlan: String,
    val redFlags: List<RedFlagAlert> = emptyList()
)

data class SendMessageResult(
    val aiResponse: String,
    val aiResponseTranslated: String? = null,
    val patientMessageOriginal: String,
    val patientMessageTranslated: String? = null,
    val redFlags: List<RedFlagAlert> = emptyList(),
    val triageLevel: String = "ROUTINE",
    val triageScore: Int = 4,
    val suggestedFollowups: List<String> = emptyList(),
    val isEmergency: Boolean = false
)

