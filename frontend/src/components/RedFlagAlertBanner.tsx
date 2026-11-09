import React from 'react';
import { ShieldAlert, ArrowRight, X } from 'lucide-react';

interface RedFlagAlertBannerProps {
  alertCount: number;
  latestAlert?: {
    patient_name: string;
    chief_complaint?: string;
    triage_level: string;
    session_id: string;
  };
  onViewAlert: (sessionId: string) => void;
  onDismiss?: () => void;
}

export const RedFlagAlertBanner: React.FC<RedFlagAlertBannerProps> = ({
  alertCount,
  latestAlert,
  onViewAlert,
  onDismiss,
}) => {
  if (alertCount <= 0 || !latestAlert) return null;

  return (
    <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white shadow-lg emergency-pulse border-b border-red-800">
      <div className="max-w-7xl mx-auto px-4 py-2.5 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-3">
            <span className="flex p-1.5 rounded-lg bg-red-800/80 ring-2 ring-white/40">
              <ShieldAlert className="h-5 w-5 text-white animate-pulse" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs uppercase font-extrabold tracking-wider bg-white text-red-700 px-2 py-0.5 rounded-md">
                  CRITICAL CLINICAL ALERT
                </span>
                <span className="text-xs text-red-100 font-medium hidden sm:inline">
                  Immediate bedside evaluation required
                </span>
              </div>
              <p className="text-sm font-semibold mt-0.5">
                Patient <span className="underline decoration-white/60">{latestAlert.patient_name}</span>:{' '}
                <span className="font-normal opacity-95">
                  {latestAlert.chief_complaint || 'Acute life-threatening symptoms detected during multilingual intake.'}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => onViewAlert(latestAlert.session_id)}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white text-red-700 hover:bg-red-50 font-bold text-xs rounded-lg shadow-sm transition-transform active:scale-95"
            >
              <span>Review Intake & SOAP</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-red-200 hover:text-white p-1 rounded-md"
                title="Dismiss banner"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

