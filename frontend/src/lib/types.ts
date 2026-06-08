export type ApplicationStatus =
  | "applied"
  | "assessment"
  | "interview_scheduled"
  | "rejected"
  | "offer_received"
  | "follow_up"
  | "unknown";

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApplicationEvent {
  id: string;
  job_application_id: string;
  email_message_id: string | null;
  event_type: string;
  title: string;
  description: string | null;
  occurred_at: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface EmailMessage {
  id: string;
  user_id: string;
  gmail_message_id: string;
  thread_id: string | null;
  subject: string;
  sender_email: string;
  received_at: string;
  raw_snippet: string | null;
  body_text: string | null;
  category: string | null;
  company_name: string | null;
  job_title: string | null;
  deadline: string | null;
  interview_date: string | null;
  action_required: boolean | null;
  summary: string | null;
  confidence_score: number | null;
  processed_at: string | null;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpcomingDeadline {
  application_id: string;
  company_name: string;
  job_title: string | null;
  deadline: string;
  deadline_type: string;
}

export interface DashboardSummary {
  total_applications: number;
  active_applications: number;
  rejected_applications: number;
  interviews_scheduled: number;
  assessments_pending: number;
  offers: number;
  follow_ups_needed: number;
  upcoming_deadlines: UpcomingDeadline[];
  recent_events: ApplicationEvent[];
}

export interface AnalyticsSummary {
  total_applications: number;
  active_applications: number;
  rejected_applications: number;
  offers: number;
  interviews: number;
  assessments: number;
  recruiter_outreach_count: number;
  response_rate: number;
  rejection_rate: number;
  interview_rate: number;
  offer_rate: number;
  average_response_time_days: number | null;
  applications_by_status: Record<string, number>;
  applications_by_company: Record<string, number>;
  events_by_type: Record<string, number>;
  weekly_application_trend: Array<{ week_start: string; count: number }>;
  recent_activity_count_7d: number;
  recent_activity_count_30d: number;
}

export interface NextAction {
  priority: "high" | "medium" | "low";
  application_id: string | null;
  company_name: string;
  job_title: string | null;
  action_type: string;
  reason: string;
  suggested_next_step: string;
  due_date: string | null;
}

export interface NextActionsResponse {
  summary: string;
  actions: NextAction[];
}

export interface JobApplicationSummary {
  id: string;
  company_name: string;
  job_title: string | null;
  status: ApplicationStatus;
  last_email_at: string | null;
  action_required: boolean;
}

export interface JobApplicationRead extends JobApplicationSummary {
  user_id: string;
  latest_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationTimeline {
  application: JobApplicationRead;
  current_status: ApplicationStatus;
  emails: EmailMessage[];
  events: ApplicationEvent[];
  next_deadline: string | null;
  next_interview_date: string | null;
}

export interface ResumeProfile {
  id: string;
  user_id: string;
  resume_text: string;
  target_roles: string[] | null;
  target_locations: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface DraftReplyResponse {
  email_id: string;
  subject: string;
  recipient_email: string;
  draft_body: string;
  tone: string;
  warnings: string[];
}

export interface MatchJobResponse {
  match_score: number;
  verdict: string;
  matched_skills: string[];
  missing_skills: string[];
  role_alignment_summary: string;
  concerns: string[];
  suggested_resume_keywords: string[];
  suggested_next_steps: string[];
}
