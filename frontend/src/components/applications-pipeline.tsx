"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import type { JobApplicationSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function ApplicationsPipeline({
  applications,
}: {
  applications: JobApplicationSummary[];
}) {
  if (applications.length === 0) {
    return (
      <EmptyState
        title="No applications yet"
        description="Seed demo data in the backend to populate the pipeline."
      />
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="hidden grid-cols-[1.4fr_1fr_140px_160px_24px] gap-4 border-b border-zinc-800 px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500 md:grid">
        <span>Company</span>
        <span>Role</span>
        <span>Status</span>
        <span>Last updated</span>
        <span />
      </div>
      <div className="divide-y divide-zinc-800">
        {applications.map((application) => (
          <Link
            key={application.id}
            href={`/applications/${application.id}`}
            className="group block transition-colors hover:bg-zinc-900/60"
          >
            <div className="grid gap-3 px-5 py-4 md:grid-cols-[1.4fr_1fr_140px_160px_24px] md:items-center md:gap-4">
              <div>
                <p className="font-medium text-zinc-100 group-hover:text-white">
                  {application.company_name}
                </p>
                {application.action_required ? (
                  <p className="mt-1 text-xs text-amber-400">Action required</p>
                ) : null}
              </div>
              <p className="text-sm text-zinc-400">
                {application.job_title ?? "Role not specified"}
              </p>
              <div>
                <StatusBadge status={application.status} />
              </div>
              <p className="text-sm text-zinc-500">{formatDate(application.last_email_at)}</p>
              <ChevronRight className="hidden h-4 w-4 text-zinc-600 group-hover:text-zinc-300 md:block" />
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}
