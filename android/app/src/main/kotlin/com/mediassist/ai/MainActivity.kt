package com.mediassist.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.mediassist.ai.network.MediAssistApiClient
import com.mediassist.ai.ui.ClinicianStationScreen
import com.mediassist.ai.ui.PatientIntakeScreen
import com.mediassist.ai.ui.theme.MediAssistAITheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MediAssistAITheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MediAssistAppRoot()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MediAssistAppRoot() {
    var selectedTab by remember { mutableStateOf(0) }
    var showServerDialog by remember { mutableStateOf(false) }
    var serverHostInput by remember { mutableStateOf(MediAssistApiClient.baseUrl) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("MediAssist AI") },
                actions = {
                    TextButton(onClick = { showServerDialog = true }) {
                        Text("⚙️ Server", style = MaterialTheme.typography.labelSmall)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Text("💬") },
                    label = { Text("Patient Intake") }
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Text("📋") },
                    label = { Text("Clinician Queue") }
                )
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (selectedTab) {
                0 -> PatientIntakeScreen(onIntakeSubmitted = { selectedTab = 1 })
                1 -> ClinicianStationScreen()
            }
        }
    }

    if (showServerDialog) {
        AlertDialog(
            onDismissRequest = { showServerDialog = false },
            confirmButton = {
                Button(onClick = {
                    MediAssistApiClient.baseUrl = serverHostInput
                    showServerDialog = false
                }) {
                    Text("Save")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerDialog = false }) {
                    Text("Cancel")
                }
            },
            title = { Text("Backend Server URL") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "Enter the FastAPI backend URL:\n• Emulator: http://10.0.2.2:8000/api\n• Physical Phone on Wi-Fi: http://192.168.31.232:8000/api",
                        style = MaterialTheme.typography.bodySmall
                    )
                    OutlinedTextField(
                        value = serverHostInput,
                        onValueChange = { serverHostInput = it },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        )
    }
}
