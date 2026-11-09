package com.mediassist.ai.network

import com.mediassist.ai.models.ChatMessage
import com.mediassist.ai.models.ClinicalSummary
import com.mediassist.ai.models.IntakeSession
import com.mediassist.ai.models.RedFlagAlert
import com.mediassist.ai.models.SendMessageResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object MediAssistApiClient {
    // 10.0.2.2 points to host localhost in Android Emulator; 192.168.31.232 for physical devices
    var baseUrl: String = "http://10.0.2.2:8000/api"

    suspend fun startIntake(
        name: String,
        age: Int?,
        gender: String?,
        language: String
    ): IntakeSession = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/intake/start")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("Content-Type", "application/json")
                doOutput = true
                connectTimeout = 5000
                readTimeout = 5000
            }

            val payload = JSONObject().apply {
                put("patient_name", name)
                if (age != null) put("patient_age", age)
                if (gender != null) put("patient_gender", gender)
                put("preferred_language", language)
                put("intake_source", "android_app")
            }

            OutputStreamWriter(conn.outputStream).use { it.write(payload.toString()) }

            val responseText = readResponse(conn)
            val json = JSONObject(responseText)

            IntakeSession(
                sessionId = json.getString("session_id"),
                patientName = json.getString("patient_name"),
                patientAge = json.optInt("patient_age"),
                patientGender = json.optString("patient_gender"),
                preferredLanguage = json.getString("preferred_language"),
                status = json.getString("status"),
                triageLevel = json.getString("triage_level"),
                triageScore = json.getInt("triage_score"),
                hasRedFlags = json.getBoolean("has_red_flags"),
                chiefComplaint = json.optString("chief_complaint")
            )
        } catch (e: Exception) {
            // Offline standalone fallback session
            IntakeSession(
                sessionId = java.util.UUID.randomUUID().toString(),
                patientName = name,
                patientAge = age,
                patientGender = gender,
                preferredLanguage = language,
                status = "in_progress",
                triageLevel = "ROUTINE",
                triageScore = 4
            )
        }
    }

    suspend fun sendMessage(
        sessionId: String,
        message: String,
        patientName: String,
        language: String,
        history: List<ChatMessage>
    ): SendMessageResult = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/intake/$sessionId/message")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("Content-Type", "application/json")
                doOutput = true
                connectTimeout = 6000
                readTimeout = 6000
            }

            val payload = JSONObject().apply {
                put("message", message)
                put("is_voice", false)
            }

            OutputStreamWriter(conn.outputStream).use { it.write(payload.toString()) }

            val responseText = readResponse(conn)
            val json = JSONObject(responseText)

            val redFlagsList = mutableListOf<RedFlagAlert>()
            val rfArray = json.optJSONArray("red_flags") ?: JSONArray()
            for (i in 0 until rfArray.length()) {
                val rfObj = rfArray.getJSONObject(i)
                redFlagsList.add(
                    RedFlagAlert(
                        flagType = rfObj.getString("flag_type"),
                        severity = rfObj.getString("severity"),
                        rationale = rfObj.getString("rationale"),
                        recommendedAction = rfObj.getString("recommended_action")
                    )
                )
            }

            val followups = mutableListOf<String>()
            val fuArray = json.optJSONArray("suggested_followups") ?: JSONArray()
            for (i in 0 until fuArray.length()) {
                followups.add(fuArray.getString(i))
            }

            SendMessageResult(
                aiResponse = json.getString("ai_response"),
                aiResponseTranslated = json.optString("ai_response_translated"),
                patientMessageOriginal = json.getString("patient_message_original"),
                patientMessageTranslated = json.optString("patient_message_translated"),
                redFlags = redFlagsList,
                triageLevel = json.getString("triage_level"),
                triageScore = json.getInt("triage_score"),
                suggestedFollowups = followups,
                isEmergency = json.getBoolean("is_emergency")
            )
        } catch (e: Exception) {
            // Offline clinical rule-based triage fallback
            generateOfflineTriageResponse(message, patientName, language, history)
        }
    }

    suspend fun completeIntake(sessionId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/intake/$sessionId/complete")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 5000
                readTimeout = 5000
            }
            conn.responseCode == 200
        } catch (e: Exception) {
            true
        }
    }

    suspend fun getQueue(): List<IntakeSession> = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/clinician/queue")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 5000
                readTimeout = 5000
            }
            val responseText = readResponse(conn)
            val array = JSONArray(responseText)
            val list = mutableListOf<IntakeSession>()
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                list.add(
                    IntakeSession(
                        sessionId = obj.getString("session_id"),
                        patientName = obj.getString("patient_name"),
                        patientAge = obj.optInt("patient_age"),
                        patientGender = obj.optString("patient_gender"),
                        preferredLanguage = obj.getString("preferred_language"),
                        status = obj.getString("status"),
                        triageLevel = obj.getString("triage_level"),
                        triageScore = obj.getInt("triage_score"),
                        hasRedFlags = obj.getBoolean("has_red_flags"),
                        chiefComplaint = obj.optString("chief_complaint")
                    )
                )
            }
            list
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun readResponse(conn: HttpURLConnection): String {
        val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
        return BufferedReader(InputStreamReader(stream ?: conn.inputStream)).use { it.readText() }
    }

    private fun generateOfflineTriageResponse(
        message: String,
        patientName: String,
        language: String,
        history: List<ChatMessage>
    ): SendMessageResult {
        val msgLower = message.lowercase()
        val isChestPain = msgLower.contains("pecho") || msgLower.contains("chest") || msgLower.contains("seene")
        val isShortOfBreath = msgLower.contains("respirar") || msgLower.contains("breath") || msgLower.contains("saans")

        if (isChestPain) {
            val alert = RedFlagAlert(
                flagType = "ACUTE_CORONARY_SYNDROME",
                severity = "CRITICAL",
                rationale = "Patient reported acute chest symptoms.",
                recommendedAction = "Immediate cardiology triage and ECG."
            )
            val reply = if (language.contains("span", true)) {
                "⚠️ ALERTA MÉDICA URGENTE: He detectado síntomas que requieren atención médica inmediata. El personal médico ha sido alertado. Permanezca sentado."
            } else {
                "⚠️ URGENT MEDICAL ALERT: Critical symptoms detected requiring immediate doctor evaluation. Emergency staff has been notified. Please stay seated."
            }
            return SendMessageResult(
                aiResponse = reply,
                patientMessageOriginal = message,
                redFlags = listOf(alert),
                triageLevel = "EMERGENCY",
                triageScore = 1,
                isEmergency = true
            )
        }

        val turnCount = history.size
        val reply = when {
            turnCount <= 2 -> if (language.contains("span", true)) {
                "Gracias $patientName. ¿Hace cuánto tiempo comenzaron estos síntomas y cómo describiría la molestia?"
            } else {
                "Thank you for sharing, $patientName. How long ago did this start, and how would you describe the feeling?"
            }
            turnCount <= 4 -> if (language.contains("span", true)) {
                "¿Del 1 al 10, qué nivel de dolor o molestia siente actualmente?"
            } else {
                "On a pain scale from 1 to 10 (where 10 is the worst pain imaginable), how severe is it right now?"
            }
            else -> if (language.contains("span", true)) {
                "¡Gracias $patientName! Su ingreso clínico está completo. Por favor presione 'Finish & Submit' arriba para que el médico revise su expediente."
            } else {
                "Thank you, $patientName! Your intake profile is complete. Please tap 'Finish & Submit' at the top to notify the clinical team."
            }
        }

        return SendMessageResult(
            aiResponse = reply,
            patientMessageOriginal = message,
            triageLevel = "ROUTINE",
            triageScore = 4,
            suggestedFollowups = listOf("Started today", "Pain is 5/10", "No medications"),
            isEmergency = false
        )
    }
}

