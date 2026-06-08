import { EmptyState } from "@/components/empty-state";
import { PriorityBadge, StatusBadge } from "@/components/status-badge";
import { MetricTile, StatCard } from "@/components/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  AnalyticsSummary,
  DashboardSummary,
  NextActionsResponse,
} from "@/lib/types";
import { formatDate, formatPercent } from "@/lib/utils";
import { SectionHeader } from "@/components/section-header";

export function DashboardOverview({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <section>
      <SectionHeader title="Overview" description="Current pipeline snapshot" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total applications" value={dashboard.total_applications} />
        <StatCard label="Active applications" value={dashboard.active_applications} />
        <StatCard
          label="Interviews scheduled"
          value={dashboard.interviews_scheduled}
          hint={`${dashboard.assessments_pending} assessments pending`}
        />
        <StatCard
          label="Offers"
          value={dashboard.offers}
          hint={`${dashboard.rejected_applications} rejected`}
        />
      </div>
    </section>
  );
}

export function NextActionsSection({ nextActions }: { nextActions: NextActionsResponse }) {
  return (
    <section>
      <SectionHeader title="Next actions" description={nextActions.summary} />
      <Card>
        <CardContent className="space-y-3 p-5">
          {nextActions.actions.length === 0 ? (
            <EmptyState
              title="No recommended actions"
              description="Your pipeline is quiet for now."
            />
          ) : (
            nextActions.actions.slice(0, 5).map((action) => (
              <div
                key={`${action.company_name}-${action.action_type}`}
                className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-zinc-100">{action.company_name}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {action.job_title ?? "Role not specified"}
                    </p>
                  </div>
                  <PriorityBadge priority={action.priority} />
                </div>
                <p className="mt-3 text-sm leading-relaxed text-zinc-400">
                  {action.suggested_next_step}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </section>
  );
}

export function DeadlinesSection({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <section>
      <SectionHeader title="Upcoming deadlines" />
      <Card>
        <CardContent className="space-y-3 p-5">
          {dashboard.upcoming_deadlines.length === 0 ? (
            <EmptyState
              title="No upcoming deadlines"
              description="Assessment and interview deadlines will appear here."
            />
          ) : (
            dashboard.upcoming_deadlines.map((deadline) => (
              <div
                key={`${deadline.application_id}-${deadline.deadline}`}
                className="flex items-start justify-between gap-4 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
              >
                <div>
                  <p className="font-medium text-zinc-100">{deadline.company_name}</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {deadline.job_title ?? "Role not specified"}
                  </p>
                </div>
                <div className="text-right">
                  <StatusBadge status={deadline.deadline_type} />
                  <p className="mt-2 text-xs text-zinc-500">{formatDate(deadline.deadline)}</p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </section>
  );
}

export function RecentActivitySection({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <section>
      <SectionHeader title="Recent activity" />
      <Card>
        <CardContent className="space-y-3 p-5">
          {dashboard.recent_events.length === 0 ? (
            <EmptyState title="No recent activity" description="Events will appear as emails sync." />
          ) : (
            dashboard.recent_events.map((event) => (
              <div
                key={event.id}
                className="flex items-start justify-between gap-4 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
              >
                <div>
                  <p className="font-medium text-zinc-100">{event.title}</p>
                  <p className="mt-1 text-xs text-zinc-500">{formatDate(event.occurred_at)}</p>
                </div>
                <StatusBadge status={event.event_type} />
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </section>
  );
}

export function AnalyticsSection({ analytics }: { analytics: AnalyticsSummary }) {
  return (
    <section>
      <SectionHeader title="Analytics" description="Conversion and activity metrics" />
      <Card>
        <CardHeader>
          <CardTitle>Pipeline performance</CardTitle>
          <CardDescription>
            {analytics.recent_activity_count_7d} events in the last 7 days ·{" "}
            {analytics.recent_activity_count_30d} in the last 30 days
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <MetricTile label="Response rate" value={formatPercent(analytics.response_rate)} />
          <MetricTile label="Interview rate" value={formatPercent(analytics.interview_rate)} />
          <MetricTile label="Offer rate" value={formatPercent(analytics.offer_rate)} />
          <MetricTile label="Rejection rate" value={formatPercent(analytics.rejection_rate)} />
          <MetricTile
            label="Avg response time"
            value={
              analytics.average_response_time_days != null
                ? `${analytics.average_response_time_days.toFixed(1)} days`
                : "—"
            }
          />
          <MetricTile
            label="Recruiter outreach"
            value={analytics.recruiter_outreach_count}
          />
        </CardContent>
      </Card>
    </section>
  );
}
