package com.mediassist.ai.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mediassist.ai.models.IntakeSession
import com.mediassist.ai.network.MediAssistApiClient
import kotlinx.coroutines.launch

@Composable
fun ClinicianStationScreen() {
    val coroutineScope = rememberCoroutineScope()
    var queue by remember { mutableStateOf(listOf<IntakeSession>()) }
    var loading by remember { mutableStateOf(true) }
    var selectedPatient by remember { mutableStateOf<IntakeSession?>(null) }

    fun refreshQueue() {
        loading = true
        coroutineScope.launch {
            queue = MediAssistApiClient.getQueue()
            loading = false
        }
    }

    LaunchedEffect(Unit) {
        refreshQueue()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Top Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Clinician Triage Station", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("Live Patient Feed & Red-Flag Triage", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            IconButton(onClick = { refreshQueue() }) {
                Text("🔄")
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (loading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return
        }

        if (queue.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No patients currently in queue.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            return
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(queue) { item ->
                val isEmergency = item.triageLevel == "EMERGENCY" || item.hasRedFlags

                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { selectedPatient = item },
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (isEmergency) Color(0xFFFFF1F2) else MaterialTheme.colorScheme.surface
                    ),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = item.patientName,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = if (isEmergency) Color(0xFF9F1239) else MaterialTheme.colorScheme.onSurface
                            )
                            Badge(
                                containerColor = when (item.triageLevel) {
                                    "EMERGENCY" -> Color(0xFFE11D48)
                                    "URGENT" -> Color(0xFFD97706)
                                    else -> Color(0xFF16A34A)
                                }
                            ) {
                                Text(
                                    text = "${item.triageLevel} (${item.triageScore})",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "${item.preferredLanguage} • Age ${item.patientAge ?: 40} • Status: ${item.status.uppercase()}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        if (!item.chiefComplaint.isNullOrBlank()) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = "Complaint: \"${item.chiefComplaint}\"",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            }
        }
    }

    // Detail Dialog
    selectedPatient?.let { p ->
        AlertDialog(
            onDismissRequest = { selectedPatient = null },
            confirmButton = {
                TextButton(onClick = { selectedPatient = null }) {
                    Text("Close")
                }
            },
            title = {
                Text("Clinical Record: ${p.patientName}", fontWeight = FontWeight.Bold)
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Language: ${p.preferredLanguage}")
                    Text("Triage: ${p.triageLevel} (Score: ${p.triageScore})")
                    if (p.hasRedFlags) {
                        Text("🚨 Red Flags Detected: Acute evaluation required.", color = Color(0xFFBE123C), fontWeight = FontWeight.Bold)
                    }
                    Text("Complaint: ${p.chiefComplaint ?: "Reported discomfort."}")
                    HorizontalDivider()
                    Text("SOAP Summary:", fontWeight = FontWeight.SemiBold)
                    Text("S: Patient presented via MediAssist intake. Reported primary symptoms in ${p.preferredLanguage}.")
                    Text("O: Triage Priority ${p.triageLevel}.")
                    Text("A: Rule out acute exacerbation.")
                    Text("P: Physician physical examination and diagnostic evaluation.")
                }
            }
        )
    }
}

