"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Inbox, KeyRound } from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { useHasToken } from "@/lib/use-auth";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label, Textarea } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const savedToken = useHasToken();
  const [token, setTokenValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleContinue() {
    const trimmed = token.trim();
    if (!trimmed) {
      setError("Paste a demo JWT token first.");
      return;
    }
    setToken(trimmed);
    router.push("/dashboard");
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
            <Inbox className="h-5 w-5 text-zinc-200" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-zinc-50">AI Job Inbox</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Portfolio demo UI for the FastAPI job-search assistant backend.
          </p>
        </div>

        {savedToken ? (
          <Card>
            <CardHeader>
              <CardTitle>Demo token saved</CardTitle>
              <CardDescription>
                A JWT is stored in localStorage for this browser session.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-3">
              <Button onClick={() => router.push("/dashboard")}>Open dashboard</Button>
              <Button variant="outline" onClick={() => router.push("/profile")}>
                View resume
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-zinc-400" />
                <CardTitle>Paste demo token</CardTitle>
              </div>
              <CardDescription>
                No Google login yet. Use the backend demo token script for local presentations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <Alert>
                <p className="font-medium text-zinc-200">Generate a demo token</p>
                <ol className="mt-2 list-decimal space-y-1 pl-5 text-zinc-400">
                  <li>Run backend migrations and seed demo data.</li>
                  <li>
                    Run{" "}
                    <code className="rounded bg-zinc-950 px-1.5 py-0.5 text-zinc-300">
                      python scripts/create_demo_token.py
                    </code>
                  </li>
                  <li>Paste the printed token below.</li>
                </ol>
                <p className="mt-3 text-xs text-zinc-500">API: {getApiBaseUrl()}</p>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="token">JWT token</Label>
                <Textarea
                  id="token"
                  value={token}
                  onChange={(event) => {
                    setTokenValue(event.target.value);
                    setError(null);
                  }}
                  placeholder="Paste Bearer token here"
                  className="min-h-[140px] font-mono text-xs"
                />
              </div>

              {error ? <Alert variant="destructive">{error}</Alert> : null}

              <Button className="w-full" onClick={handleContinue}>
                Continue to dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
