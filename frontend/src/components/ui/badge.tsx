import type * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
  {
    variants: {
      variant: {
        default: "border-zinc-700 bg-zinc-800/80 text-zinc-300",
        success: "border-emerald-900/60 bg-emerald-950/50 text-emerald-300",
        warning: "border-amber-900/60 bg-amber-950/50 text-amber-300",
        danger: "border-red-900/60 bg-red-950/50 text-red-300",
        info: "border-blue-900/60 bg-blue-950/50 text-blue-300",
        purple: "border-violet-900/60 bg-violet-950/50 text-violet-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
