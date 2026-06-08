import type { ApplicationStatus } from "@/lib/types";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "purple";

const STATUS_VARIANTS: Record<ApplicationStatus | string, BadgeVariant> = {
  applied: "info",
  assessment: "warning",
  interview_scheduled: "purple",
  rejected: "danger",
  offer_received: "success",
  follow_up: "warning",
  unknown: "default",
  application_confirmation: "info",
  interview_invitation: "purple",
  recruiter_outreach: "info",
  offer: "success",
  rejection: "danger",
  follow_up_needed: "warning",
  status_update: "default",
  irrelevant: "default",
  strong_match: "success",
  moderate_match: "info",
  weak_match: "warning",
  unclear: "default",
};

export function getStatusVariant(status: string): BadgeVariant {
  return STATUS_VARIANTS[status] ?? "default";
}

export function getPriorityVariant(priority: string): BadgeVariant {
  if (priority === "high") return "danger";
  if (priority === "medium") return "warning";
  return "default";
}
