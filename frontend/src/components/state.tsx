import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/30 p-12">
      <div className="flex items-center gap-3 text-sm text-zinc-400">
        <Loader2 className="h-4 w-4 animate-spin" />
        {message}
      </div>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6">
      <p className="text-sm font-medium text-red-200">Something went wrong</p>
      <p className="mt-1 text-sm text-red-300/80">{message}</p>
      {onRetry ? (
        <Button variant="destructive" size="sm" className="mt-4" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
