import type * as React from "react";
import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "destructive" | "success";
}) {
  return (
    <div
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        variant === "destructive" && "border-red-900/60 bg-red-950/30 text-red-200",
        variant === "success" && "border-emerald-900/60 bg-emerald-950/30 text-emerald-200",
        variant === "default" && "border-zinc-800 bg-zinc-900/80 text-zinc-300",
        className,
      )}
      {...props}
    />
  );
}
