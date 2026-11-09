import React, { useState } from 'react';
import { FileText, Save, Check, Printer, Edit3, ShieldCheck } from 'lucide-react';
import type { ClinicalSummary } from '../types';

interface SoapNoteEditorProps {
  summary: ClinicalSummary;
  sessionId: string;
  patientName: string;
  onSave: (updatedData: {
    soap_subjective: string;
    soap_objective: string;
    soap_assessment: string;
    soap_plan: string;
    clinician_notes: string;
  }) => Promise<void>;
}

export const SoapNoteEditor: React.FC<SoapNoteEditorProps> = ({
  summary,
  sessionId,
  patientName,
  onSave,
}) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [subjective, setSubjective] = useState<string>(summary.soap_subjective || '');
  const [objective, setObjective] = useState<string>(summary.soap_objective || '');
  const [assessment, setAssessment] = useState<string>(summary.soap_assessment || '');
  const [plan, setPlan] = useState<string>(summary.soap_plan || '');
  const [clinicianNotes, setClinicianNotes] = useState<string>(summary.clinician_notes || '');
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        soap_subjective: subjective,
        soap_objective: objective,
        soap_assessment: assessment,
        soap_plan: plan,
        clinician_notes: clinicianNotes,
      });
      setIsEditing(false);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert('Failed to save SOAP note.');
    } finally {
      setSaving(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 print:shadow-none print:border-none">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Standardized Clinical SOAP Note</h3>
            <p className="text-xs text-slate-500">
              Synthesized by Gemini AI & Verified by Attending Clinician
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 print:hidden">
          <button
            onClick={handlePrint}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print EHR Record</span>
          </button>

          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 text-white hover:bg-slate-800 text-xs font-semibold"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Note</span>
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center space-x-1 px-4 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 text-xs font-semibold shadow-sm"
            >
              {saving ? (
                <span>Saving...</span>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save & Approve</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {savedSuccess && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-medium flex items-center space-x-2">
          <Check className="w-4 h-4 text-emerald-600" />
          <span>SOAP note approved and saved to clinical record successfully.</span>
        </div>
      )}

      {/* SOAP Sections */}
      <div className="grid grid-cols-1 gap-6">
        {/* Subjective */}
        <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              S — Subjective (Patient History & Reported Symptoms)
            </span>
          </div>
          {isEditing ? (
            <textarea
              value={subjective}
              onChange={(e) => setSubjective(e.target.value)}
              rows={3}
              className="w-full text-xs text-slate-800 bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          ) : (
            <p className="text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
              {subjective || 'No subjective symptoms documented.'}
            </p>
          )}
        </div>

        {/* Objective */}
        <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              O — Objective (Triage Observations & Clinical Severity)
            </span>
          </div>
          {isEditing ? (
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={3}
              className="w-full text-xs text-slate-800 bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          ) : (
            <p className="text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
              {objective || 'No objective findings documented.'}
            </p>
          )}
        </div>

        {/* Assessment */}
        <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              A — Assessment (Differential Diagnosis & Triage Rationale)
            </span>
          </div>
          {isEditing ? (
            <textarea
              value={assessment}
              onChange={(e) => setAssessment(e.target.value)}
              rows={3}
              className="w-full text-xs text-slate-800 bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          ) : (
            <p className="text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
              {assessment || 'Assessment pending clinician review.'}
            </p>
          )}
        </div>

        {/* Plan */}
        <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              P — Plan (Immediate Actions, Diagnostics & Therapeutics)
            </span>
          </div>
          {isEditing ? (
            <textarea
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              rows={3}
              className="w-full text-xs text-slate-800 bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          ) : (
            <p className="text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
              {plan || 'Clinical plan pending attending physician review.'}
            </p>
          )}
        </div>

        {/* Clinician Direct Notes */}
        <div className="bg-indigo-50/40 p-4 rounded-xl border border-indigo-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>Attending Physician Addendum & Orders</span>
            </span>
          </div>
          {isEditing ? (
            <textarea
              value={clinicianNotes}
              onChange={(e) => setClinicianNotes(e.target.value)}
              placeholder="Enter direct bedside observations, order numbers, or instructions..."
              rows={2}
              className="w-full text-xs text-slate-800 bg-white border border-indigo-200 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          ) : (
            <p className="text-xs leading-relaxed text-indigo-950 whitespace-pre-wrap italic">
              {clinicianNotes || 'No physician addendum noted yet.'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
