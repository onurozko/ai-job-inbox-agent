import { StatusBadge } from "@/components/status-badge";
import type { ApplicationEvent } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function EventTimeline({ events }: { events: ApplicationEvent[] }) {
  if (events.length === 0) {
    return null;
  }

  return (
    <div className="relative space-y-0">
      <div className="absolute bottom-2 left-[11px] top-2 w-px bg-zinc-800" />
      {events.map((event) => (
        <div key={event.id} className="relative flex gap-4 pb-6 last:pb-0">
          <div className="relative z-10 mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-950">
            <span className="h-2 w-2 rounded-full bg-zinc-400" />
          </div>
          <div className="min-w-0 flex-1 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-zinc-100">{event.title}</p>
                <p className="mt-1 text-xs text-zinc-500">{formatDate(event.occurred_at)}</p>
              </div>
              <StatusBadge status={event.event_type} />
            </div>
            {event.description ? (
              <p className="mt-3 text-sm leading-relaxed text-zinc-400">{event.description}</p>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
