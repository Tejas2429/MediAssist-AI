import axios from 'axios';
import type {
  DashboardStats,
  QueueItem,
  PatientDetailResponse,
  IntakeSession,
  SendMessageResponse,
  User
} from '../types';

const API_BASE = 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('mediassist_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('mediassist_token', res.data.access_token);
      localStorage.setItem('mediassist_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },
  getCurrentUser: async (): Promise<User> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('mediassist_token');
    localStorage.removeItem('mediassist_user');
  },

  // Intake
  startIntake: async (data: {
    patient_name: string;
    patient_age?: number;
    patient_gender?: string;
    preferred_language: string;
    mrn?: string;
  }): Promise<IntakeSession> => {
    const res = await apiClient.post('/intake/start', data);
    return res.data;
  },
  sendMessage: async (
    sessionId: string,
    message: string,
    isVoice: boolean = false
  ): Promise<SendMessageResponse> => {
    const res = await apiClient.post(`/intake/${sessionId}/message`, {
      message,
      is_voice: isVoice,
    });
    return res.data;
  },
  completeIntake: async (sessionId: string) => {
    const res = await apiClient.post(`/intake/${sessionId}/complete`);
    return res.data;
  },
  getIntakeStatus: async (sessionId: string) => {
    const res = await apiClient.get(`/intake/${sessionId}/status`);
    return res.data;
  },

  // Clinician
  getDashboardStats: async (): Promise<DashboardStats> => {
    const res = await apiClient.get('/clinician/dashboard-stats');
    return res.data;
  },
  getQueue: async (params?: {
    triage_level?: string;
    status?: string;
    language?: string;
    search?: string;
  }): Promise<QueueItem[]> => {
    const res = await apiClient.get('/clinician/queue', { params });
    return res.data;
  },
  getPatientDetail: async (sessionId: string): Promise<PatientDetailResponse> => {
    const res = await apiClient.get(`/clinician/patient/${sessionId}`);
    return res.data;
  },
  updateSoapNote: async (
    sessionId: string,
    soapData: {
      soap_subjective?: string;
      soap_objective?: string;
      soap_assessment?: string;
      soap_plan?: string;
      clinician_notes?: string;
      status?: string;
    }
  ) => {
    const res = await apiClient.put(`/clinician/intake/${sessionId}/soap`, soapData);
    return res.data;
  },
  updateTriage: async (
    sessionId: string,
    data: {
      triage_level: string;
      triage_score: number;
      rationale?: string;
    }
  ) => {
    const res = await apiClient.put(`/clinician/intake/${sessionId}/triage`, data);
    return res.data;
  },

  // Red Flags
  getActiveRedFlags: async () => {
    const res = await apiClient.get('/red-flags/active');
    return res.data;
  },
  acknowledgeRedFlag: async (sessionId: string) => {
    const res = await apiClient.post(`/red-flags/acknowledge/${sessionId}`);
    return res.data;
  },
};
