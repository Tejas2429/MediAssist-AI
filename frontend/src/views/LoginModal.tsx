import React, { useState } from 'react';
import { X, Lock, Mail, Stethoscope, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import type { User } from '../types';

interface LoginModalProps {
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ onClose, onSuccess }) => {
  const [email, setEmail] = useState('doctor@mediassist.ai');
  const [password, setPassword] = useState('doctor123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await api.login(email, password);
      onSuccess(data.user);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 p-6 text-white text-center relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/30 flex items-center justify-center mx-auto mb-2 text-indigo-300">
            <Stethoscope className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold">Clinician Station Sign-In</h3>
          <p className="text-xs text-indigo-200 mt-1">
            Access secure HIPAA clinical records, triage queues, and SOAP approvals
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 font-medium">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Quick Demo Credentials Autofill */}
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
            <span className="font-bold text-slate-700 flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Demo Physician Credentials:</span>
            </span>
            <div className="flex justify-between text-slate-500 font-mono text-[11px]">
              <span>User: doctor@mediassist.ai</span>
              <span>Pass: doctor123</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-100 transition-all flex items-center justify-center space-x-2"
          >
            {loading ? <span>Verifying...</span> : <span>Sign In as Clinician</span>}
          </button>
        </form>
      </div>
    </div>
  );
};
