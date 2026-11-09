# MediAssist AI — Native Android Application 📱
> **Multilingual Patient Intake & Clinical Triage Companion**  
> *Built with Kotlin, Jetpack Compose, Material 3, Android SpeechRecognizer & TextToSpeech.*

---

## 🌟 Key Features

1. **Multilingual Conversational Intake**:
   - Native Jetpack Compose conversational UI.
   - Languages: **English**, **Spanish (Español)**, **Hindi (हिन्दी)**, **French (Français)**, and **Mandarin (中文)**.
   - Quick patient persona selection (e.g. Maria - Chest Pain, Rajesh - Asthma, Tejas - Knee Pain).
2. **Native Speech-to-Text & Text-to-Speech**:
   - **Voice Input**: Tap the 🎤 button to dictate symptoms in your chosen language using Android's native `SpeechRecognizer`.
   - **Read-Aloud**: Tap **🔊 Listen** on any AI message to hear the response read aloud via Android `TextToSpeech`.
3. **Real-Time Red-Flag Alert Card**:
   - Flashing emergency card when acute life-threatening symptoms (STEMI, Stroke, Severe Dyspnea, Anaphylaxis) are detected.
4. **Clinician Triage Station Tab**:
   - Switch between **Patient Intake** and **Clinician Queue** using the bottom navigation bar.
   - Live color-coded ESI priority badges (Emergency Red, Urgent Amber, Routine Green).
   - Side-by-side original language vs English translation review and SOAP note viewer.
5. **Configurable Server Endpoint**:
   - Tap **⚙️ Server** at the top right to configure the backend URL:
     - **Android Emulator**: `http://10.0.2.2:8000/api`
     - **Physical Device over Wi-Fi**: `http://192.168.31.232:8000/api`
   - **Offline Resilience**: Embedded fallback triage engine ensures patient safety even when disconnected from Wi-Fi!

---

## 🚀 How to Open in Android Studio

1. Open **Android Studio**.
2. Click **Open** and select the folder:
   ```
   c:\Users\tejas\Downloads\medi\android
   ```
3. Allow Gradle to sync.
4. Select an Android Virtual Device (AVD) or connect your physical Android phone via USB (with USB Debugging enabled).
5. Click **Run ▶ (Shift + F10)**.

---

## 🛠️ CLI Build & Run

From PowerShell:
```powershell
# Set Java Home to Android Studio's bundled JDK
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio1\jbr"

# Build Debug APK
cd android
.\gradlew.bat assembleDebug

# Output APK is located at:
# android/app/build/outputs/apk/debug/app-debug.apk
```

