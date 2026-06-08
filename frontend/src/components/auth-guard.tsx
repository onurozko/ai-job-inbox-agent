"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { hasToken } from "@/lib/auth";
import { LoadingState } from "@/components/state";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasToken()) {
      router.replace("/");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return <LoadingState message="Checking demo token..." />;
  }

  return <>{children}</>;
}
