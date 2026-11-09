import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  ShieldAlert,
  Globe,
  User,
  HeartPulse,
  CheckCircle,
  Volume2,
  RefreshCw,
  HelpCircle,
  PhoneCall
} from 'lucide-react';
import { api } from '../services/api';
import { VoiceInput, speakText } from '../components/VoiceInput';
import { TriageBadge } from '../components/TriageBadge';
import type { IntakeSession, RedFlagAlert } from '../types';

interface Message {
  sender: 'patient' | 'ai_assistant';
  text: string;
  translatedText?: string;
  isVoice?: boolean;
}

const SUPPORTED_LANGUAGES = [
  { name: 'English', flag: '🇺🇸', label: 'English' },
  { name: 'Spanish', flag: '🇪🇸', label: 'Español' },
  { name: 'Hindi', flag: '🇮🇳', label: 'हिन्दी' },
  { name: 'French', flag: '🇫🇷', label: 'Français' },
  { name: 'Mandarin', flag: '🇨🇳', label: '中文' },
  { name: 'Arabic', flag: '🇸🇦', label: 'العربية' },
  { name: 'German', flag: '🇩🇪', label: 'Deutsch' },
];

export const PatientIntakeView: React.FC = () => {
  const [session, setSession] = useState<IntakeSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [activeRedFlags, setActiveRedFlags] = useState<RedFlagAlert[]>([]);
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([]);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Intake Form details before starting
  const [patientName, setPatientName] = useState('Carlos Mendez');
  const [patientAge, setPatientAge] = useState<number | ''>(52);
  const [patientGender, setPatientGender] = useState('Male');
  const [selectedLanguage, setSelectedLanguage] = useState('Spanish');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeRedFlags]);

  const handleStartIntake = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!patientName.trim()) return;

    setLoading(true);
    try {
      const newSession = await api.startIntake({
        patient_name: patientName,
        patient_age: patientAge ? Number(patientAge) : undefined,
        patient_gender: patientGender,
        preferred_language: selectedLanguage,
      });
      setSession(newSession);

      // Fetch initial greeting
      const statusData = await api.getIntakeStatus(newSession.session_id);
      if (statusData.messages && statusData.messages.length > 0) {
        setMessages(
          statusData.messages.map((m: any) => ({
            sender: m.sender,
            text: m.original_text,
            translatedText: m.translated_text,
          }))
        );
      }
    } catch (err) {
      console.error(err);
      alert('Failed to initialize intake session. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || !session || loading) return;

    // Optimistically append patient message
    const updatedMessages: Message[] = [
      ...messages,
      { sender: 'patient', text, isVoice: isListening },
    ];
    setMessages(updatedMessages);
    setInputText('');
    setLoading(true);

    try {
      const response = await api.sendMessage(session.session_id, text, isListening);

      // Update messages with AI response
      setMessages([
        ...updatedMessages,
        {
          sender: 'ai_assistant',
          text: response.ai_response,
          translatedText: response.ai_response_translated,
        },
      ]);

      // Set red flags and suggestions
      if (response.red_flags && response.red_flags.length > 0) {
        setActiveRedFlags(response.red_flags);
      }
      if (response.suggested_followups) {
        setSuggestedFollowups(response.suggested_followups);
      }

      // Auto-read aloud if patient preference
      if (isListening || response.is_emergency) {
        speakText(response.ai_response, selectedLanguage);
      }
    } catch (err) {
      console.error(err);
      alert('Error communicating with clinical assistant.');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteIntake = async () => {
    if (!session) return;
    setLoading(true);
    try {
      await api.completeIntake(session.session_id);
      setIsSubmitted(true);
    } catch (err) {
      console.error(err);
      alert('Failed to complete intake submission.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = () => {
    setSession(null);
    setMessages([]);
    setActiveRedFlags([]);
    setSuggestedFollowups([]);
    setIsSubmitted(false);
  };

  // 1. Initial Intake Setup Form
  if (!session) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-sky-600 via-indigo-600 to-sky-700 p-8 text-white text-center">
            <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center mx-auto mb-4 border border-white/30 shadow-inner">
              <HeartPulse className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight">Patient Intake Companion</h2>
            <p className="text-sky-100 text-sm mt-1 max-w-md mx-auto">
              Please choose your language. MediAssist AI will guide you through your medical intake with compassionate assistance.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleStartIntake} className="p-8 space-y-6">
            {/* Language Selector */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Preferred Language / Idioma / भाषा / Langue / 语言
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <button
                    key={lang.name}
                    type="button"
                    onClick={() => setSelectedLanguage(lang.name)}
                    className={`flex items-center space-x-2 px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                      selectedLanguage === lang.name
                        ? 'border-sky-600 bg-sky-50 text-sky-800 ring-2 ring-sky-200'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span className="text-lg">{lang.flag}</span>
                    <span>{lang.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Patient Name */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Patient Full Name
              </label>
              <input
                type="text"
                required
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="e.g. Maria Rodriguez"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>

            {/* Age & Gender */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Age (Optional)
                </label>
                <input
                  type="number"
                  value={patientAge}
                  onChange={(e) => setPatientAge(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="e.g. 48"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Gender (Optional)
                </label>
                <select
                  value={patientGender}
                  onChange={(e) => setPatientGender(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white"
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Non-binary">Non-binary</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
              </div>
            </div>

            {/* Quick Demo Presets */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-2">
                💡 Try Pre-filled Demo Persona:
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setPatientName('Maria Rodriguez');
                    setPatientAge(58);
                    setPatientGender('Female');
                    setSelectedLanguage('Spanish');
                  }}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-sky-400 text-slate-700"
                >
                  🇪🇸 Maria (Chest pain test)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPatientName('Rajesh Sharma');
                    setPatientAge(42);
                    setPatientGender('Male');
                    setSelectedLanguage('Hindi');
                  }}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-sky-400 text-slate-700"
                >
                  🇮🇳 Rajesh (Asthma / Hindi)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPatientName('Jean-Luc Moreau');
                    setPatientAge(62);
                    setPatientGender('Male');
                    setSelectedLanguage('French');
                  }}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-sky-400 text-slate-700"
                >
                  🇫🇷 Jean-Luc (Stroke test)
                </button>
              </div>
            </div>

            {/* Submit Start */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-sky-600 to-indigo-600 text-white hover:from-sky-700 hover:to-indigo-700 shadow-md shadow-sky-200 transition-all flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span>Starting intake...</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Begin Clinical Intake in {selectedLanguage}</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // 2. Completed Intake View
  if (isSubmitted) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <div className="bg-white rounded-3xl border border-slate-200 shadow-xl p-8 space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
            <CheckCircle className="w-10 h-10" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Intake Successfully Submitted!</h2>
            <p className="text-slate-600 text-sm mt-2">
              Thank you, <span className="font-semibold text-slate-800">{session.patient_name}</span>. Your clinical intake details and translated conversation have been transmitted directly to our attending clinical team.
            </p>
          </div>

          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-left text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Session ID:</span>
              <span className="font-mono text-slate-700">{session.session_id.substring(0, 8)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Primary Language:</span>
              <span className="font-semibold text-slate-800">{session.preferred_language}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Triage Classification:</span>
              <TriageBadge level={session.triage_level} score={session.triage_score} size="sm" />
            </div>
          </div>

          <button
            onClick={handleResetSession}
            className="w-full py-3 px-4 rounded-xl bg-slate-900 text-white font-semibold text-sm hover:bg-slate-800 transition-colors flex items-center justify-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Start New Patient Intake</span>
          </button>
        </div>
      </div>
    );
  }

  // 3. Active Chat Intake View
  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Session Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 mb-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm">
            <User className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-900 text-base">{session.patient_name}</span>
              <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium">
                {session.preferred_language}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              {session.patient_age ? `${session.patient_age} yrs • ` : ''}
              {session.patient_gender || 'Patient'} • Kiosk Session
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <TriageBadge level={session.triage_level} score={session.triage_score} />
          <button
            onClick={handleCompleteIntake}
            className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-transform active:scale-95"
          >
            Finish & Submit
          </button>
        </div>
      </div>

      {/* Emergency Red Flag Notice if Detected */}
      {activeRedFlags.length > 0 && (
        <div className="mb-4 p-4 rounded-2xl bg-red-50 border-2 border-red-400 text-red-900 shadow-md emergency-pulse">
          <div className="flex items-start space-x-3">
            <ShieldAlert className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-sm uppercase tracking-wide text-red-800">
                🚨 Emergency Alert Triggered
              </h4>
              <p className="text-xs mt-1 leading-relaxed text-red-700">
                We have notified our emergency medical response team immediately. Please stay seated where you are. Clinical staff is en route to evaluate you at once.
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {activeRedFlags.map((flag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-1 rounded-md text-[11px] font-semibold bg-red-200 text-red-800"
                  >
                    {flag.flag_type}: {flag.recommended_action}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Messages Container */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-md overflow-hidden flex flex-col h-[520px]">
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.map((msg, index) => {
            const isAI = msg.sender === 'ai_assistant';
            return (
              <div
                key={index}
                className={`flex items-start space-x-3 ${isAI ? 'justify-start' : 'justify-end'}`}
              >
                {isAI && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <HeartPulse className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[80%] rounded-2xl p-4 shadow-xs text-sm leading-relaxed ${
                    isAI
                      ? 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200/80'
                      : 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-tr-none shadow-md shadow-sky-100'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Audio read-aloud button for AI reply */}
                  {isAI && (
                    <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-500">
                      <button
                        onClick={() => speakText(msg.text, selectedLanguage)}
                        className="flex items-center space-x-1 hover:text-sky-600 transition-colors"
                        title="Listen to audio"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span className="text-[11px]">Listen</span>
                      </button>

                      {msg.translatedText && (
                        <span className="text-[10px] text-slate-400 italic">
                          (Translated for Clinicians)
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {!isAI && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center space-x-3 text-slate-400 text-xs py-2">
              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                <Sparkles className="w-4 h-4 animate-spin text-sky-600" />
              </div>
              <span className="italic">MediAssist AI is reviewing and translating...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Quick Follow-Up Chips */}
        {suggestedFollowups.length > 0 && !loading && (
          <div className="px-4 py-2 bg-slate-50/80 border-t border-slate-200 flex flex-wrap gap-2 items-center">
            <span className="text-[10px] uppercase font-bold text-slate-400">Quick reply:</span>
            {suggestedFollowups.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(suggestion)}
                className="text-xs px-3 py-1 rounded-full bg-white border border-slate-200 hover:border-sky-400 hover:text-sky-700 text-slate-700 shadow-2xs transition-all active:scale-95"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Chat Input Bar */}
        <div className="p-4 bg-white border-t border-slate-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            {/* Voice Input Button */}
            <VoiceInput
              onTranscript={(transcript) => {
                setInputText(transcript);
                handleSendMessage(transcript);
              }}
              language={selectedLanguage}
              isListening={isListening}
              setIsListening={setIsListening}
            />

            {/* Text Input */}
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={
                isListening
                  ? 'Listening to your voice...'
                  : `Type your symptoms in ${selectedLanguage}...`
              }
              className="flex-1 px-4 py-3 rounded-full border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />

            {/* Send Button */}
            <button
              type="submit"
              disabled={loading || !inputText.trim()}
              className="p-3 rounded-full bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white shadow-md shadow-sky-200 transition-all active:scale-95 flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
