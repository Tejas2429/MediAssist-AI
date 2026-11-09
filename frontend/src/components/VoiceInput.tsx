import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  language: string;
  isListening: boolean;
  setIsListening: (val: boolean) => void;
}

const LANG_CODE_MAP: Record<string, string> = {
  Spanish: 'es-ES',
  Hindi: 'hi-IN',
  French: 'fr-FR',
  Mandarin: 'zh-CN',
  Arabic: 'ar-SA',
  German: 'de-DE',
  English: 'en-US',
};

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  language,
  isListening,
  setIsListening,
}) => {
  const [hasSpeechSupport, setHasSpeechSupport] = useState<boolean>(false);
  const [recognitionInstance, setRecognitionInstance] = useState<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setHasSpeechSupport(true);
      const recognizer = new SpeechRecognition();
      recognizer.continuous = false;
      recognizer.interimResults = false;

      recognizer.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          onTranscript(transcript);
        }
        setIsListening(false);
      };

      recognizer.onerror = (e: any) => {
        console.warn('Speech recognition error:', e);
        setIsListening(false);
      };

      recognizer.onend = () => {
        setIsListening(false);
      };

      setRecognitionInstance(recognizer);
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionInstance) {
      alert('Speech recognition is not supported in this browser. Please use keyboard input.');
      return;
    }

    if (isListening) {
      recognitionInstance.stop();
      setIsListening(false);
    } else {
      const code = LANG_CODE_MAP[language] || 'en-US';
      recognitionInstance.lang = code;
      try {
        recognitionInstance.start();
        setIsListening(true);
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
      }
    }
  };

  return (
    <button
      type="button"
      onClick={toggleListening}
      title={isListening ? 'Stop recording voice' : `Speak in ${language}`}
      className={`p-3 rounded-full transition-all flex items-center justify-center ${
        isListening
          ? 'bg-red-500 text-white animate-pulse ring-4 ring-red-200'
          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
      }`}
    >
      {isListening ? <Mic className="w-5 h-5" /> : <Mic className="w-5 h-5 text-slate-600" />}
    </button>
  );
};

export const speakText = (text: string, language: string) => {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const code = LANG_CODE_MAP[language] || 'en-US';
  utterance.lang = code;
  window.speechSynthesis.speak(utterance);
};

