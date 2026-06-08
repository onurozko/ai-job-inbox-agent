const TOKEN_KEY = "job_inbox_demo_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token.trim());
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("job-inbox-auth-change"));
  }
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("job-inbox-auth-change"));
  }
}

export function hasToken(): boolean {
  return Boolean(getToken());
}
