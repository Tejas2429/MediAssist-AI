import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Globe,
  ChevronRight,
  Eye,
  CheckCircle2,
  AlertOctagon
} from 'lucide-react';
import { api } from '../services/api';
import type { DashboardStats, QueueItem } from '../types';
import { TriageBadge } from '../components/TriageBadge';
import { ClinicianDetailModal } from './ClinicianDetailModal';

interface ClinicianDashboardViewProps {
  onOpenPatientDetail?: (sessionId: string) => void;
}

export const ClinicianDashboardView: React.FC<ClinicianDashboardViewProps> = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [triageFilter, setTriageFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [languageFilter, setLanguageFilter] = useState<string>('ALL');

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, queueData] = await Promise.all([
        api.getDashboardStats(),
        api.getQueue({
          triage_level: triageFilter,
          status: statusFilter,
          language: languageFilter,
          search: searchTerm || undefined,
        }),
      ]);
      setStats(statsData);
      setQueue(queueData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Auto-poll queue every 15 seconds for live emergency updates
    const interval = setInterval(fetchDashboardData, 15000);
    return () => clearInterval(interval);
  }, [triageFilter, statusFilter, languageFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDashboardData();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title & Refresh */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Clinician Intake & Triage Station
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time patient intake queue, automated translations, and AI red-flag detection.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="font-semibold">Live Patient Feed</span>
          </span>
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Refresh queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Critical Red Flags */}
          <div className="bg-white rounded-2xl border border-red-200 p-5 shadow-xs relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-red-600">
                Acute Red Flags
              </span>
              <div className="p-2 rounded-xl bg-red-100 text-red-600">
                <ShieldAlert className="w-5 h-5 animate-pulse" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {stats.critical_red_flags}
              </span>
              <span className="text-xs font-medium text-red-600">Immediate attention</span>
            </div>
          </div>

          {/* Card 2: Active in Queue */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Waiting In Queue
              </span>
              <div className="p-2 rounded-xl bg-sky-100 text-sky-600">
                <Users className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {stats.active_in_queue}
              </span>
              <span className="text-xs text-slate-500">patients waiting</span>
            </div>
          </div>

          {/* Card 3: Urgent & Emergency */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">
                Urgent Priority
              </span>
              <div className="p-2 rounded-xl bg-amber-100 text-amber-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {stats.urgent_triages}
              </span>
              <span className="text-xs text-slate-500">ESI Level 2/3</span>
            </div>
          </div>

          {/* Card 4: Reviewed Intakes */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
                Reviewed & SOAP Signed
              </span>
              <div className="p-2 rounded-xl bg-emerald-100 text-emerald-600">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {stats.reviewed_count}
              </span>
              <span className="text-xs text-slate-500">completed today</span>
            </div>
          </div>
        </div>
      )}

      {/* Multilingual Volume Distribution */}
      {stats && stats.languages_breakdown && (
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Globe className="w-4 h-4 text-indigo-600" />
            <span>Multilingual Intake Volume:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.languages_breakdown).map(([lang, count]) => (
              <span
                key={lang}
                className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center space-x-1"
              >
                <span>{lang}:</span>
                <span className="font-bold text-indigo-600">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs space-y-3">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search */}
          <form onSubmit={handleSearchSubmit} className="flex-1 w-full relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by patient name, symptoms, or chief complaint..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </form>

          {/* Triage Level Filter */}
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <span className="text-xs text-slate-500 font-medium">Triage:</span>
            <select
              value={triageFilter}
              onChange={(e) => setTriageFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Categories</option>
              <option value="EMERGENCY">Emergency (ESI 1-2)</option>
              <option value="URGENT">Urgent (ESI 3)</option>
              <option value="ROUTINE">Routine (ESI 4-5)</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="escalated">Escalated (Red Flag)</option>
              <option value="submitted">Submitted</option>
              <option value="in_progress">In Progress</option>
              <option value="reviewed">Reviewed</option>
            </select>
          </div>

          {/* Language Filter */}
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <span className="text-xs text-slate-500 font-medium">Language:</span>
            <select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Languages</option>
              <option value="Spanish">Spanish</option>
              <option value="Hindi">Hindi</option>
              <option value="English">English</option>
              <option value="French">French</option>
              <option value="Mandarin">Mandarin</option>
            </select>
          </div>
        </div>
      </div>

      {/* Patient Queue Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
                <th className="py-3.5 px-6">Patient Name</th>
                <th className="py-3.5 px-4">Triage Priority</th>
                <th className="py-3.5 px-4">Primary Language</th>
                <th className="py-3.5 px-6">Chief Complaint & Symptoms</th>
                <th className="py-3.5 px-4">Wait Time</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {queue.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No intake records matching current filter criteria.
                  </td>
                </tr>
              ) : (
                queue.map((item) => {
                  const isEmergency = item.triage_level === 'EMERGENCY' || item.has_red_flags;

                  return (
                    <tr
                      key={item.session_id}
                      onClick={() => setSelectedSessionId(item.session_id)}
                      className={`hover:bg-slate-50/80 transition-colors cursor-pointer ${
                        isEmergency ? 'bg-red-50/40' : ''
                      }`}
                    >
                      {/* Patient Name */}
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-3">
                          {item.has_red_flags && (
                            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0 animate-pulse" />
                          )}
                          <div>
                            <div className="font-bold text-slate-900 text-sm">{item.patient_name}</div>
                            <div className="text-[11px] text-slate-500">
                              {item.patient_age ? `${item.patient_age} yo • ` : ''}
                              {item.patient_gender || 'Adult'}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Triage Badge */}
                      <td className="py-4 px-4">
                        <TriageBadge level={item.triage_level} score={item.triage_score} size="sm" />
                      </td>

                      {/* Language */}
                      <td className="py-4 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-xs font-medium">
                          {item.preferred_language}
                        </span>
                      </td>

                      {/* Chief Complaint */}
                      <td className="py-4 px-6 max-w-xs">
                        <p className="text-slate-700 truncate font-medium">
                          {item.chief_complaint || 'No complaint recorded.'}
                        </p>
                      </td>

                      {/* Wait Time */}
                      <td className="py-4 px-4 whitespace-nowrap text-slate-500">
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>{item.wait_time_minutes} min ago</span>
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-4 px-4">
                        <span
                          className={`text-[11px] font-bold uppercase px-2 py-0.5 rounded-md ${
                            item.status === 'escalated'
                              ? 'bg-red-100 text-red-800'
                              : item.status === 'reviewed'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>

                      {/* Action */}
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedSessionId(item.session_id);
                          }}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Review</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedSessionId && (
        <ClinicianDetailModal
          sessionId={selectedSessionId}
          onClose={() => setSelectedSessionId(null)}
          onRefreshQueue={fetchDashboardData}
        />
      )}
    </div>
  );
};
