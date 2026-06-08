"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Mail } from "lucide-react";
import { AssistantToolsPanel } from "@/components/assistant-tools-panel";
import { AuthGuard } from "@/components/auth-guard";
import { EventTimeline } from "@/components/event-timeline";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { ErrorState, LoadingState } from "@/components/state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import {
  createDraftReply,
  fetchApplicationTimeline,
  matchJob,
} from "@/lib/services";
import type { ApplicationTimeline, DraftReplyResponse, MatchJobResponse } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const applicationId = params.id;

  const [timeline, setTimeline] = useState<ApplicationTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<DraftReplyResponse | null>(null);
  const [matchResult, setMatchResult] = useState<MatchJobResponse | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadTimeline = useCallback(async () => {
    if (!applicationId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApplicationTimeline(applicationId);
      setTimeline(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load application");
    } finally {
      setLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    void loadTimeline();
  }, [loadTimeline]);

  async function handleDraftReply(emailId: string) {
    setActionLoading(`draft-${emailId}`);
    setActionError(null);
    try {
      const response = await createDraftReply(emailId);
      setDraft(response);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to generate draft");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleMatchJob() {
    if (!applicationId) return;
    setActionLoading("match");
    setActionError(null);
    try {
      const response = await matchJob({
        job_application_id: applicationId,
        job_description: jobDescription.trim() || undefined,
      });
      setMatchResult(response);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to run job match");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <AuthGuard>
      <div className="space-y-8">
        <Link
          href="/applications"
          className="inline-flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-zinc-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to applications
        </Link>

        {loading ? <LoadingState message="Loading application..." /> : null}
        {error ? <ErrorState message={error} onRetry={() => void loadTimeline()} /> : null}

        {!loading && !error && timeline ? (
          <>
            <PageHeader
              title={timeline.application.company_name}
              description={timeline.application.job_title ?? "Role not specified"}
              action={<StatusBadge status={timeline.current_status} />}
            />

            <div className="grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Timeline</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EventTimeline events={timeline.events} />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Related emails</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {timeline.emails.length === 0 ? (
                      <EmptyState title="No linked emails" />
                    ) : (
                      timeline.emails.map((email) => (
                        <div
                          key={email.id}
                          className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <Mail className="h-4 w-4 text-zinc-500" />
                                <p className="font-medium text-zinc-100">{email.subject}</p>
                              </div>
                              <p className="mt-1 text-xs text-zinc-500">
                                {email.sender_email} · {formatDate(email.received_at)}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={actionLoading === `draft-${email.id}`}
                              onClick={() => void handleDraftReply(email.id)}
                            >
                              {actionLoading === `draft-${email.id}` ? "Drafting..." : "Draft reply"}
                            </Button>
                          </div>
                          {email.body_text ? (
                            <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-zinc-400">
                              {email.body_text}
                            </p>
                          ) : null}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </div>

              <AssistantToolsPanel
                jobDescription={jobDescription}
                onJobDescriptionChange={setJobDescription}
                onMatchJob={() => void handleMatchJob()}
                matchLoading={actionLoading === "match"}
                matchResult={matchResult}
                draft={draft}
                actionError={actionError}
              />
            </div>
          </>
        ) : null}
      </div>
    </AuthGuard>
  );
}
