export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  department: string;
  is_active: boolean;
  created_at: string;
}

export interface RedFlagAlert {
  flag_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE';
  rationale: string;
  recommended_action: string;
}

export interface IntakeSession {
  id: number;
  session_id: string;
  patient_name: string;
  patient_age?: number;
  patient_gender?: string;
  preferred_language: string;
  status: 'in_progress' | 'submitted' | 'reviewed' | 'escalated';
  triage_level: 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'SELF_CARE';
  triage_score: number;
  has_red_flags: boolean;
  chief_complaint?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  sender: 'patient' | 'ai_assistant' | 'system';
  language: string;
  original_text: string;
  translated_text?: string;
  is_voice: boolean;
  created_at: string;
}

export interface ClinicalSummary {
  id: number;
  session_id: string;
  patient_id?: number;
  chief_complaint?: string;
  hpi?: string;
  onset?: string;
  severity_scale: number;
  current_medications: any;
  allergies: any;
  review_of_systems: any;
  red_flags_detected: RedFlagAlert[];
  triage_rationale?: string;
  soap_subjective?: string;
  soap_objective?: string;
  soap_assessment?: string;
  soap_plan?: string;
  clinician_notes?: string;
  reviewed_by?: number;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_intakes_today: number;
  active_in_queue: number;
  critical_red_flags: number;
  urgent_triages: number;
  routine_triages: number;
  reviewed_count: number;
  average_wait_minutes: number;
  languages_breakdown: Record<string, number>;
}

export interface QueueItem {
  session_id: string;
  patient_name: string;
  patient_age?: number;
  patient_gender?: string;
  preferred_language: string;
  status: string;
  triage_level: 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'SELF_CARE';
  triage_score: number;
  has_red_flags: boolean;
  chief_complaint?: string;
  red_flags_count: number;
  wait_time_minutes: number;
  created_at: string;
}

export interface PatientDetailResponse {
  intake_session: IntakeSession;
  messages: ChatMessage[];
  clinical_summary?: ClinicalSummary;
}

export interface SendMessageResponse {
  ai_response: string;
  ai_response_translated?: string;
  patient_message_original: string;
  patient_message_translated?: string;
  red_flags: RedFlagAlert[];
  triage_level: string;
  triage_score: number;
  suggested_followups: string[];
  is_emergency: boolean;
}

