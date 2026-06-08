"use client";

import { useSyncExternalStore } from "react";
import { getToken, hasToken } from "@/lib/auth";

const AUTH_CHANGE_EVENT = "job-inbox-auth-change";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(AUTH_CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(AUTH_CHANGE_EVENT, callback);
  };
}

export function useHasToken(): boolean {
  return useSyncExternalStore(subscribe, hasToken, () => false);
}

export function useToken(): string | null {
  return useSyncExternalStore(subscribe, getToken, () => null);
}
