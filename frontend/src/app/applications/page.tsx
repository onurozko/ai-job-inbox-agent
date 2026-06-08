"use client";

import { useCallback, useEffect, useState } from "react";
import { ApplicationsPipeline } from "@/components/applications-pipeline";
import { AuthGuard } from "@/components/auth-guard";
import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/state";
import { fetchApplications } from "@/lib/services";
import type { JobApplicationSummary } from "@/lib/types";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<JobApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchApplications();
      setApplications(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load applications");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadApplications();
  }, [loadApplications]);

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PageHeader
          title="Applications"
          description="Track companies, statuses, and open each timeline for assistant tools."
        />

        {loading ? <LoadingState message="Loading applications..." /> : null}
        {error ? <ErrorState message={error} onRetry={() => void loadApplications()} /> : null}

        {!loading && !error ? <ApplicationsPipeline applications={applications} /> : null}
      </div>
    </AuthGuard>
  );
}
