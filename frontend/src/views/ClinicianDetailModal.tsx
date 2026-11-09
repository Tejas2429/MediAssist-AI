import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldAlert,
  Globe,
  Clock,
  User,
  HeartPulse,
  Languages,
  CheckCircle,
  FileCheck,
  AlertTriangle,
  Stethoscope
} from 'lucide-react';
import { api } from '../services/api';
import type { PatientDetailResponse } from '../types';
import { TriageBadge } from '../components/TriageBadge';
import { SoapNoteEditor } from '../components/SoapNoteEditor';

interface ClinicianDetailModalProps {
  sessionId: string;
  onClose: () => void;
  onRefreshQueue: () => void;
}

export const ClinicianDetailModal: React.FC<ClinicianDetailModalProps> = ({
  sessionId,
  onClose,
  onRefreshQueue,
}) => {
  const [data, setData] = useState<PatientDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showOriginalLang, setShowOriginalLang] = useState<boolean>(false);
  const [overridingTriage, setOverridingTriage] = useState<boolean>(false);
  const [selectedTriage, setSelectedTriage] = useState<string>('EMERGENCY');

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await api.getPatientDetail(sessionId);
      setData(res);
      setSelectedTriage(res.intake_session.triage_level);
    } catch (err) {
      console.error(err);
      alert('Failed to load patient detail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [sessionId]);

  const handleSaveSoap = async (updatedData: any) => {
    await api.updateSoapNote(sessionId, updatedData);
    await fetchDetail();
    onRefreshQueue();
  };

  const handleUpdateTriage = async () => {
    let score = 3;
    if (selectedTriage === 'EMERGENCY') score = 1;
    if (selectedTriage === 'URGENT') score = 2;
    if (selectedTriage === 'ROUTINE') score = 4;
    if (selectedTriage === 'SELF_CARE') score = 5;

    try {
      await api.updateTriage(sessionId, {
        triage_level: selectedTriage,
        triage_score: score,
        rationale: 'Attending physician manual triage adjustment',
      });
      setOverridingTriage(false);
      await fetchDetail();
      onRefreshQueue();
    } catch (err) {
      alert('Failed to update triage level.');
    }
  };

  const handleAcknowledge = async () => {
    try {
      await api.acknowledgeRedFlag(sessionId);
      alert('Red flag acknowledged and logged in HIPAA audit trail.');
    } catch (err) {
      console.error(err);
    }
  };

  if (loading || !data) {
    return (
      <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-700">Loading Clinical Intake Record...</p>
        </div>
      </div>
    );
  }

  const { intake_session, messages, clinical_summary } = data;
  const redFlags = clinical_summary?.red_flags_detected || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 overflow-y-auto">
      <div className="bg-slate-50 rounded-3xl border border-slate-200 shadow-2xl w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden my-auto">
        {/* Modal Header */}
        <div className="bg-white px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-lg">
              <User className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-xl font-bold text-slate-900">{intake_session.patient_name}</h2>
                <TriageBadge
                  level={intake_session.triage_level}
                  score={intake_session.triage_score}
                  size="md"
                />
                <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium">
                  {intake_session.status.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                <span>Age: {intake_session.patient_age || 'N/A'}</span>
                <span>•</span>
                <span>Gender: {intake_session.patient_gender || 'N/A'}</span>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <Globe className="w-3.5 h-3.5 text-slate-400" />
                  <span>Language: {intake_session.preferred_language}</span>
                </span>
                <span>•</span>
                <span className="font-mono text-[11px] text-slate-400">
                  ID: {intake_session.session_id.substring(0, 8)}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {intake_session.has_red_flags && (
              <button
                onClick={handleAcknowledge}
                className="px-3 py-1.5 rounded-xl bg-red-100 hover:bg-red-200 text-red-800 text-xs font-semibold flex items-center space-x-1 transition-colors"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Acknowledge Alert</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (5 cols): Multilingual Conversation Log */}
          <div className="lg:col-span-5 flex flex-col space-y-4">
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex-1 flex flex-col">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div className="flex items-center space-x-2">
                  <Languages className="w-4 h-4 text-indigo-600" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Multilingual Intake Dialogue
                  </span>
                </div>

                {/* Translation Toggle */}
                <button
                  onClick={() => setShowOriginalLang(!showOriginalLang)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium transition-colors"
                >
                  {showOriginalLang ? 'Show English Translation' : 'Show Original Language'}
                </button>
              </div>

              {/* Chat Log */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[500px]">
                {messages.map((m) => {
                  const isPatient = m.sender === 'patient';
                  const displayText = showOriginalLang
                    ? m.original_text
                    : m.translated_text || m.original_text;

                  return (
                    <div
                      key={m.id}
                      className={`p-3 rounded-xl text-xs leading-relaxed ${
                        isPatient
                          ? 'bg-slate-100 border border-slate-200/80 text-slate-900 ml-3'
                          : 'bg-indigo-50/70 border border-indigo-100 text-indigo-950 mr-3'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1 text-[10px] text-slate-400">
                        <span className="font-bold uppercase tracking-wider">
                          {isPatient ? `Patient (${m.language})` : 'MediAssist AI'}
                        </span>
                        <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="whitespace-pre-wrap">{displayText}</p>
                      {!showOriginalLang && m.language !== 'English' && isPatient && (
                        <p className="mt-1 pt-1 border-t border-slate-200/50 text-[10px] text-slate-500 italic">
                          Original: "{m.original_text}"
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Triage Adjustment Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                  <Stethoscope className="w-4 h-4 text-indigo-600" />
                  <span>Clinical Triage Adjustment</span>
                </span>
                {!overridingTriage && (
                  <button
                    onClick={() => setOverridingTriage(true)}
                    className="text-xs text-indigo-600 hover:underline font-medium"
                  >
                    Adjust
                  </button>
                )}
              </div>

              {overridingTriage ? (
                <div className="space-y-3 pt-2">
                  <div className="grid grid-cols-2 gap-2">
                    {['EMERGENCY', 'URGENT', 'ROUTINE', 'SELF_CARE'].map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => setSelectedTriage(lvl)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg border text-center transition-all ${
                          selectedTriage === lvl
                            ? 'bg-indigo-600 text-white border-indigo-600'
                            : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => setOverridingTriage(false)}
                      className="px-3 py-1 rounded-lg text-xs text-slate-600 hover:bg-slate-100"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleUpdateTriage}
                      className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700"
                    >
                      Confirm Triage
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <span>Current: <strong>{intake_session.triage_level}</strong> (ESI {intake_session.triage_score})</span>
                  <span className="text-slate-400">Attending physician verified</span>
                </div>
              )}
            </div>
          </div>

          {/* Right Column (7 cols): Clinical Summary, Red Flags & SOAP Note */}
          <div className="lg:col-span-7 space-y-4">
            {/* Red Flag Alert Card if detected */}
            {redFlags.length > 0 && (
              <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-4 shadow-sm emergency-pulse">
                <div className="flex items-start space-x-3">
                  <ShieldAlert className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
                  <div className="w-full">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-red-800">
                        Critical Red Flags Identified ({redFlags.length})
                      </h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-200 text-red-800">
                        HIGH PRIORITY
                      </span>
                    </div>

                    <div className="mt-2 space-y-2">
                      {redFlags.map((flag, idx) => (
                        <div key={idx} className="bg-white/90 p-2.5 rounded-xl border border-red-200 text-xs space-y-1">
                          <div className="font-bold text-red-900 flex items-center space-x-1.5">
                            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                            <span>{flag.flag_type}</span>
                          </div>
                          <p className="text-slate-700 text-[11px] leading-relaxed">
                            <span className="font-semibold text-slate-800">Clinical Rationale:</span> {flag.rationale}
                          </p>
                          <p className="text-red-700 text-[11px] leading-relaxed font-medium">
                            <span className="font-semibold">Stat Action:</span> {flag.recommended_action}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Structured Medical Attributes (Chief complaint, HPI, Meds, Allergies) */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-3">
                Structured Clinical Extraction
              </span>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Severity Scale</span>
                  <span className="text-slate-900 font-extrabold text-sm">
                    {clinical_summary?.severity_scale || 5} / 10
                  </span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Onset</span>
                  <span className="text-slate-900 font-semibold truncate block">
                    {clinical_summary?.onset || 'Acute'}
                  </span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 sm:col-span-2">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Allergies</span>
                  <span className="text-slate-900 font-medium truncate block">
                    {Array.isArray(clinical_summary?.allergies)
                      ? clinical_summary?.allergies.join(', ')
                      : 'None documented'}
                  </span>
                </div>
              </div>

              <div className="text-xs space-y-2">
                <div>
                  <span className="font-bold text-slate-700">Chief Complaint:</span>{' '}
                  <span className="text-slate-800 font-medium">
                    {clinical_summary?.chief_complaint || intake_session.chief_complaint || 'None'}
                  </span>
                </div>
                <div>
                  <span className="font-bold text-slate-700">History of Present Illness (HPI):</span>{' '}
                  <span className="text-slate-700 leading-relaxed">
                    {clinical_summary?.hpi || 'HPI synthesis pending intake progression.'}
                  </span>
                </div>
              </div>
            </div>

            {/* Standardized SOAP Note Editor */}
            {clinical_summary && (
              <SoapNoteEditor
                summary={clinical_summary}
                sessionId={sessionId}
                patientName={intake_session.patient_name}
                onSave={handleSaveSoap}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
