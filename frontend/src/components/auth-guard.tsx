"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useHasToken } from "@/lib/use-auth";
import { LoadingState } from "@/components/state";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const hasAuth = useHasToken();

  useEffect(() => {
    if (!hasAuth) {
      router.replace("/");
    }
  }, [hasAuth, router]);

  if (!hasAuth) {
    return <LoadingState message="Checking demo token..." />;
  }

  return <>{children}</>;
}
