"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import {
  AnalyticsSection,
  DashboardOverview,
  DeadlinesSection,
  NextActionsSection,
  RecentActivitySection,
} from "@/components/dashboard-sections";
import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/state";
import {
  fetchAnalyticsSummary,
  fetchDashboardSummary,
  fetchNextActions,
} from "@/lib/services";
import type { AnalyticsSummary, DashboardSummary, NextActionsResponse } from "@/lib/types";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [nextActions, setNextActions] = useState<NextActionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardData, analyticsData, actionsData] = await Promise.all([
        fetchDashboardSummary(),
        fetchAnalyticsSummary(),
        fetchNextActions(),
      ]);
      setDashboard(dashboardData);
      setAnalytics(analyticsData);
      setNextActions(actionsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PageHeader
          title="Dashboard"
          description="Pipeline overview, analytics, and AI-assisted next steps."
        />

        {loading ? <LoadingState message="Loading dashboard..." /> : null}
        {error ? <ErrorState message={error} onRetry={() => void loadData()} /> : null}

        {!loading && !error && dashboard && analytics && nextActions ? (
          <div className="space-y-8">
            <DashboardOverview dashboard={dashboard} />
            <div className="grid gap-8 xl:grid-cols-2">
              <NextActionsSection nextActions={nextActions} />
              <DeadlinesSection dashboard={dashboard} />
            </div>
            <div className="grid gap-8 xl:grid-cols-2">
              <RecentActivitySection dashboard={dashboard} />
              <AnalyticsSection analytics={analytics} />
            </div>
          </div>
        ) : null}
      </div>
    </AuthGuard>
  );
}
