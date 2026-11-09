import React from 'react';
import {
  HeartPulse,
  LayoutDashboard,
  MessageSquare,
  ShieldAlert,
  User,
  LogOut,
  Stethoscope
} from 'lucide-react';
import type { User as UserType } from '../types';

interface NavbarProps {
  currentView: 'intake' | 'clinician';
  onViewChange: (view: 'intake' | 'clinician') => void;
  criticalAlertCount: number;
  currentUser: UserType | null;
  onLoginClick: () => void;
  onLogoutClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onViewChange,
  criticalAlertCount,
  currentUser,
  onLoginClick,
  onLogoutClick,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-xs backdrop-blur-md bg-white/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-200">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">MediAssist</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-sky-100 text-sky-800 border border-sky-200">
                  AI Clinical Suite
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Multilingual Intake & Real-Time Red-Flag Triage
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => onViewChange('intake')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentView === 'intake'
                  ? 'bg-white text-sky-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Patient Intake Companion</span>
            </button>
            <button
              onClick={() => onViewChange('clinician')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all relative ${
                currentView === 'clinician'
                  ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Clinician Dashboard</span>
              {criticalAlertCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-red-600 text-white text-[10px] font-bold emergency-pulse">
                  {criticalAlertCount}
                </span>
              )}
            </button>
          </div>

          {/* Right Action / Auth */}
          <div className="flex items-center space-x-3">
            {criticalAlertCount > 0 && (
              <div
                onClick={() => onViewChange('clinician')}
                className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs font-semibold cursor-pointer hover:bg-red-100 transition-colors"
              >
                <ShieldAlert className="w-4 h-4 text-red-600 animate-bounce" />
                <span>{criticalAlertCount} Acute Red Flag{criticalAlertCount > 1 ? 's' : ''}</span>
              </div>
            )}

            {currentUser ? (
              <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
                <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                  <Stethoscope className="w-4 h-4" />
                </div>
                <div className="text-left hidden lg:block">
                  <div className="text-xs font-semibold text-slate-800 leading-tight">
                    {currentUser.full_name}
                  </div>
                  <div className="text-[10px] text-slate-500">{currentUser.department}</div>
                </div>
                <button
                  onClick={onLogoutClick}
                  title="Sign out"
                  className="p-1 hover:text-red-600 text-slate-400 transition-colors ml-1"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 shadow-sm transition-all"
              >
                <User className="w-3.5 h-3.5" />
                <span>Clinician Login</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
