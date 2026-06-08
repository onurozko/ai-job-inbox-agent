import { Badge } from "@/components/ui/badge";
import { getPriorityVariant, getStatusVariant } from "@/lib/status-styles";
import { formatStatus } from "@/lib/utils";

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={getStatusVariant(status)}>{formatStatus(status)}</Badge>;
}

export function PriorityBadge({ priority }: { priority: string }) {
  return <Badge variant={getPriorityVariant(priority)}>{priority}</Badge>;
}
