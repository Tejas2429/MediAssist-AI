import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { RedFlagAlertBanner } from './components/RedFlagAlertBanner';
import { PatientIntakeView } from './views/PatientIntakeView';
import { ClinicianDashboardView } from './views/ClinicianDashboardView';
import { LoginModal } from './views/LoginModal';
import { api } from './services/api';
import type { User } from './types';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'intake' | 'clinician'>('clinician');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoginOpen, setIsLoginOpen] = useState<boolean>(false);
  const [activeAlerts, setActiveAlerts] = useState<any[]>([]);
  const [showEmergencyBanner, setShowEmergencyBanner] = useState<boolean>(true);

  // Load existing session if present
  useEffect(() => {
    const savedUser = localStorage.getItem('mediassist_user');
    if (savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('mediassist_user');
      }
    }
  }, []);

  // Poll for active red flags
  const checkActiveRedFlags = async () => {
    try {
      const alerts = await api.getActiveRedFlags();
      setActiveAlerts(alerts);
    } catch (e) {
      // Backend might still be starting
    }
  };

  useEffect(() => {
    checkActiveRedFlags();
    const interval = setInterval(checkActiveRedFlags, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
  };

  const handleViewAlert = (sessionId: string) => {
    setCurrentView('clinician');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Critical Red Flag Alert Banner */}
      {showEmergencyBanner && activeAlerts.length > 0 && (
        <RedFlagAlertBanner
          alertCount={activeAlerts.length}
          latestAlert={activeAlerts[0]}
          onViewAlert={handleViewAlert}
          onDismiss={() => setShowEmergencyBanner(false)}
        />
      )}

      {/* Main Navbar */}
      <Navbar
        currentView={currentView}
        onViewChange={(view) => setCurrentView(view)}
        criticalAlertCount={activeAlerts.length}
        currentUser={currentUser}
        onLoginClick={() => setIsLoginOpen(true)}
        onLogoutClick={handleLogout}
      />

      {/* Main View Area */}
      <main className="flex-1 pb-16">
        {currentView === 'intake' ? (
          <PatientIntakeView />
        ) : (
          <ClinicianDashboardView />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-800">MediAssist AI</span>
            <span>• Multilingual Clinical Intake, Translation & Triage Workflows</span>
          </div>
          <div className="flex items-center space-x-4 text-slate-400">
            <span>FastAPI Backend</span>
            <span>•</span>
            <span>React & Vite</span>
            <span>•</span>
            <span>PostgreSQL & SQLite Dual Engine</span>
            <span>•</span>
            <span>Google Gemini AI</span>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {isLoginOpen && (
        <LoginModal
          onClose={() => setIsLoginOpen(false)}
          onSuccess={(user) => setCurrentUser(user)}
        />
      )}
    </div>
  );
};

export default App;
