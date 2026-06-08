"use client";

import { Sparkles, Wand2 } from "lucide-react";
import { CopyBlock } from "@/components/copy-block";
import { StatusBadge } from "@/components/status-badge";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import type { DraftReplyResponse, MatchJobResponse } from "@/lib/types";

export function AssistantToolsPanel({
  jobDescription,
  onJobDescriptionChange,
  onMatchJob,
  matchLoading,
  matchResult,
  draft,
  actionError,
}: {
  jobDescription: string;
  onJobDescriptionChange: (value: string) => void;
  onMatchJob: () => void;
  matchLoading: boolean;
  matchResult: MatchJobResponse | null;
  draft: DraftReplyResponse | null;
  actionError: string | null;
}) {
  return (
    <div className="space-y-4">
      <Card className="border-zinc-800 bg-gradient-to-br from-zinc-900/80 to-zinc-950/80">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-zinc-300" />
            <CardTitle>Job match assistant</CardTitle>
          </div>
          <CardDescription>
            Compare your stored resume against this application and optional pasted description.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={jobDescription}
            onChange={(event) => onJobDescriptionChange(event.target.value)}
            placeholder="Optional: paste a job description to combine with application context"
            className="min-h-[100px]"
          />
          <Button onClick={onMatchJob} disabled={matchLoading}>
            <Wand2 className="h-4 w-4" />
            {matchLoading ? "Running match..." : "Run job match"}
          </Button>
          {matchResult ? (
            <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge status={matchResult.verdict} />
                <span className="text-sm font-medium text-zinc-200">
                  Score {matchResult.match_score}/100
                </span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-400">
                {matchResult.role_alignment_summary}
              </p>
              {matchResult.matched_skills.length > 0 ? (
                <p className="text-sm text-zinc-500">
                  Matched: {matchResult.matched_skills.join(", ")}
                </p>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {actionError ? <Alert variant="destructive">{actionError}</Alert> : null}

      {draft ? (
        <Card>
          <CardHeader>
            <CardTitle>Generated reply draft</CardTitle>
            <CardDescription>
              To: {draft.recipient_email} · Subject: {draft.subject}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <CopyBlock content={draft.draft_body} />
            {draft.warnings.length > 0 ? (
              <Alert variant="destructive">
                <ul className="list-disc space-y-1 pl-4">
                  {draft.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </Alert>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
