import { apiFetch } from "@/lib/api";
import type {
  AnalyticsSummary,
  ApplicationTimeline,
  DashboardSummary,
  DraftReplyResponse,
  MatchJobResponse,
  NextActionsResponse,
  PaginatedResponse,
  ResumeProfile,
  JobApplicationSummary,
} from "@/lib/types";

export function fetchDashboardSummary() {
  return apiFetch<DashboardSummary>("/dashboard/summary");
}

export function fetchAnalyticsSummary() {
  return apiFetch<AnalyticsSummary>("/analytics/summary");
}

export function fetchNextActions() {
  return apiFetch<NextActionsResponse>("/assistant/next-actions");
}

export function fetchApplications(page = 1, pageSize = 50) {
  return apiFetch<PaginatedResponse<JobApplicationSummary>>(
    `/applications?page=${page}&page_size=${pageSize}`,
  );
}

export function fetchApplicationTimeline(applicationId: string) {
  return apiFetch<ApplicationTimeline>(`/applications/${applicationId}/timeline`);
}

export function fetchResumeProfile() {
  return apiFetch<ResumeProfile>("/profile/resume");
}

export function updateResumeProfile(payload: {
  resume_text: string;
  target_roles?: string[] | null;
  target_locations?: string[] | null;
}) {
  return apiFetch<ResumeProfile>("/profile/resume", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function createDraftReply(emailId: string) {
  return apiFetch<DraftReplyResponse>("/assistant/draft-reply", {
    method: "POST",
    body: JSON.stringify({ email_id: emailId, tone: "professional" }),
  });
}

export function matchJob(payload: {
  job_application_id?: string;
  job_description?: string;
}) {
  return apiFetch<MatchJobResponse>("/assistant/match-job", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
