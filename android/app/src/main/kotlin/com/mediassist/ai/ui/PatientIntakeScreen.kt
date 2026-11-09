package com.mediassist.ai.ui

import android.app.Activity
import android.content.Intent
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mediassist.ai.models.ChatMessage
import com.mediassist.ai.models.IntakeSession
import com.mediassist.ai.models.RedFlagAlert
import com.mediassist.ai.network.MediAssistApiClient
import kotlinx.coroutines.launch
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientIntakeScreen(
    onIntakeSubmitted: () -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var session by remember { mutableStateOf<IntakeSession?>(null) }
    var messages by remember { mutableStateOf(listOf<ChatMessage>()) }
    var inputText by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var activeRedFlags by remember { mutableStateOf(listOf<RedFlagAlert>()) }
    var suggestedFollowups by remember { mutableStateOf(listOf<String>()) }
    var isSubmitted by remember { mutableStateOf(false) }

    // Patient Setup State
    var patientName by remember { mutableStateOf("Tejas V") }
    var patientAge by remember { mutableStateOf("22") }
    var selectedLanguage by remember { mutableStateOf("English") }

    // TextToSpeech setup
    var tts by remember { mutableStateOf<TextToSpeech?>(null) }
    DisposableEffect(Unit) {
        val ttsInstance = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale.ENGLISH
            }
        }
        tts = ttsInstance
        onDispose {
            ttsInstance.stop()
            ttsInstance.shutdown()
        }
    }

    // Speech to Text Launcher
    val speechLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val spokenText = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if (!spokenText.isNullOrBlank()) {
                inputText = spokenText
            }
        }
    }

    fun startListening() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            val langTag = when (selectedLanguage) {
                "Spanish" -> "es-ES"
                "Hindi" -> "hi-IN"
                "French" -> "fr-FR"
                "Mandarin" -> "zh-CN"
                else -> "en-US"
            }
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, langTag)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak your symptoms in $selectedLanguage...")
        }
        speechLauncher.launch(intent)
    }

    fun speak(text: String) {
        val loc = when (selectedLanguage) {
            "Spanish" -> Locale("es", "ES")
            "Hindi" -> Locale("hi", "IN")
            "French" -> Locale.FRENCH
            "Mandarin" -> Locale.CHINESE
            else -> Locale.ENGLISH
        }
        tts?.language = loc
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
    }

    fun sendMessage(msgText: String) {
        val text = msgText.trim()
        val currentSession = session ?: return
        if (text.isBlank() || loading) return

        val userMsg = ChatMessage(
            sender = "patient",
            originalText = text,
            language = selectedLanguage
        )
        messages = messages + userMsg
        inputText = ""
        loading = true

        coroutineScope.launch {
            val result = MediAssistApiClient.sendMessage(
                sessionId = currentSession.sessionId,
                message = text,
                patientName = currentSession.patientName,
                language = selectedLanguage,
                history = messages
            )

            val aiMsg = ChatMessage(
                sender = "ai_assistant",
                originalText = result.aiResponse,
                translatedText = result.aiResponseTranslated,
                language = selectedLanguage
            )
            messages = messages + aiMsg
            if (result.redFlags.isNotEmpty()) {
                activeRedFlags = result.redFlags
                currentSession.hasRedFlags = true
                currentSession.triageLevel = result.triageLevel
                currentSession.triageScore = result.triageScore
            }
            suggestedFollowups = result.suggestedFollowups
            loading = false

            // Auto-speak in emergencies or user preference
            if (result.isEmergency) {
                speak(result.aiResponse)
            }
        }
    }

    if (session == null) {
        // Setup / Registration Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "MediAssist AI - Patient Intake",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = "Multilingual digital clinical companion for triage and registration.",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                // Language Chips
                Text("Select Preferred Language:", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val langs = listOf("English", "Spanish", "Hindi", "French", "Mandarin")
                    items(langs) { lang ->
                        FilterChip(
                            selected = selectedLanguage == lang,
                            onClick = { selectedLanguage = lang },
                            label = { Text(lang) }
                        )
                    }
                }

                OutlinedTextField(
                    value = patientName,
                    onValueChange = { patientName = it },
                    label = { Text("Patient Full Name") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = patientAge,
                    onValueChange = { patientAge = it },
                    label = { Text("Age") },
                    modifier = Modifier.fillMaxWidth()
                )

                // Quick Personas
                Text("💡 Quick Personas:", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(
                        onClick = {
                            patientName = "Maria Rodriguez"
                            patientAge = "58"
                            selectedLanguage = "Spanish"
                        },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text("🇪🇸 Maria (Chest Pain)", fontSize = 11.sp)
                    }
                    OutlinedButton(
                        onClick = {
                            patientName = "Rajesh Sharma"
                            patientAge = "42"
                            selectedLanguage = "Hindi"
                        },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text("🇮🇳 Rajesh (Asthma)", fontSize = 11.sp)
                    }
                }

                Button(
                    onClick = {
                        loading = true
                        coroutineScope.launch {
                            val newSession = MediAssistApiClient.startIntake(
                                name = patientName,
                                age = patientAge.toIntOrNull(),
                                gender = "Male",
                                language = selectedLanguage
                            )
                            session = newSession

                            val greeting = when (selectedLanguage) {
                                "Spanish" -> "¡Hola, $patientName! Soy su asistente médico virtual MediAssist AI. ¿Cuál es el motivo principal de su consulta hoy?"
                                "Hindi" -> "नमस्ते $patientName! मैं MediAssist AI हूँ। आज आपकी क्या समस्या या तकलीफ है?"
                                "French" -> "Bonjour $patientName ! Je suis MediAssist AI. Quelle est la raison de votre visite aujourd'hui ?"
                                else -> "Hello $patientName! I am MediAssist AI, your clinical intake companion. What symptoms are you experiencing today?"
                            }
                            messages = listOf(
                                ChatMessage(sender = "ai_assistant", originalText = greeting, language = selectedLanguage)
                            )
                            loading = false
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("Begin Clinical Intake")
                }
            }
        }
        return
    }

    if (isSubmitted) {
        // Confirmation Screen
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            shape = RoundedCornerShape(24.dp)
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text("Intake Submitted Successfully! ✅", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Text(
                    "Your symptoms and clinical translation have been sent directly to the attending physician.",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Button(onClick = {
                    session = null
                    messages = emptyList()
                    activeRedFlags = emptyList()
                    isSubmitted = false
                }) {
                    Text("Start New Intake")
                }
            }
        }
        return
    }

    // Active Intake Chat
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp)
    ) {
        // Top Header
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(session?.patientName ?: "", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Text("${session?.preferredLanguage} • Triage: ${session?.triageLevel}", fontSize = 12.sp)
                }
                Button(
                    onClick = {
                        coroutineScope.launch {
                            MediAssistApiClient.completeIntake(session!!.sessionId)
                            isSubmitted = true
                            onIntakeSubmitted()
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF16A34A))
                ) {
                    Text("Finish & Submit", fontSize = 12.sp)
                }
            }
        }

        // Red Flag Alert Banner if detected
        if (activeRedFlags.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFFE4E6)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("🚨 CRITICAL EMERGENCY ALERT", color = Color(0xFFBE123C), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    Text("Staff notified. Please remain seated calmly.", color = Color(0xFF9F1239), fontSize = 12.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Messages List
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages) { msg ->
                val isPatient = msg.sender == "patient"
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (isPatient) Arrangement.End else Arrangement.Start
                ) {
                    Box(
                        modifier = Modifier
                            .widthIn(max = 280.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .background(if (isPatient) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant)
                            .padding(12.dp)
                    ) {
                        Column {
                            Text(
                                text = msg.originalText,
                                color = if (isPatient) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 14.sp
                            )
                            if (!isPatient) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 4.dp),
                                    horizontalArrangement = Arrangement.End
                                ) {
                                    Text(
                                        text = "🔊 Listen",
                                        fontSize = 11.sp,
                                        color = MaterialTheme.colorScheme.primary,
                                        modifier = Modifier.clickable { speak(msg.originalText) }
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }

        // Suggested Follow-up Chips
        if (suggestedFollowups.isNotEmpty() && !loading) {
            LazyRow(
                modifier = Modifier.padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(suggestedFollowups) { suggestion ->
                    SuggestionChip(
                        onClick = { sendMessage(suggestion) },
                        label = { Text(suggestion, fontSize = 11.sp) }
                    )
                }
            }
        }

        // Input Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            IconButton(
                onClick = { startListening() },
                modifier = Modifier.background(MaterialTheme.colorScheme.surfaceVariant, CircleShape)
            ) {
                Text("🎤", fontSize = 18.sp)
            }

            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                placeholder = { Text("Type symptoms in $selectedLanguage...", fontSize = 12.sp) },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(24.dp)
            )

            Button(
                onClick = { sendMessage(inputText) },
                enabled = inputText.isNotBlank() && !loading,
                shape = CircleShape,
                contentPadding = PaddingValues(12.dp)
            ) {
                Text("➤")
            }
        }
    }
}

