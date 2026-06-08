"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/state";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { fetchResumeProfile, updateResumeProfile } from "@/lib/services";
import type { ResumeProfile } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function parseList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function ChipPreview({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 pt-2">
      {items.map((item) => (
        <Badge key={item} variant="default">
          {item}
        </Badge>
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ResumeProfile | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [targetRoles, setTargetRoles] = useState("");
  const [targetLocations, setTargetLocations] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const roleChips = useMemo(() => parseList(targetRoles), [targetRoles]);
  const locationChips = useMemo(() => parseList(targetLocations), [targetLocations]);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchResumeProfile();
      setProfile(data);
      setResumeText(data.resume_text);
      setTargetRoles((data.target_roles ?? []).join(", "));
      setTargetLocations((data.target_locations ?? []).join(", "));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load resume profile");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await updateResumeProfile({
        resume_text: resumeText,
        target_roles: roleChips,
        target_locations: locationChips,
      });
      setProfile(updated);
      setMessage("Resume profile saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save resume profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PageHeader
          title="Resume profile"
          description="Manage the resume text used for AI job matching in the demo."
        />

        {loading ? <LoadingState message="Loading resume profile..." /> : null}
        {error ? <ErrorState message={error} onRetry={() => void loadProfile()} /> : null}

        {!loading && !error ? (
          <Card>
            <CardHeader>
              <CardTitle>Stored resume</CardTitle>
              {profile ? (
                <CardDescription>Last updated {formatDate(profile.updated_at)}</CardDescription>
              ) : null}
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="resume">Resume text</Label>
                <Textarea
                  id="resume"
                  value={resumeText}
                  onChange={(event) => setResumeText(event.target.value)}
                  className="min-h-[320px] font-mono text-xs leading-relaxed"
                />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="roles">Target roles</Label>
                  <Input
                    id="roles"
                    value={targetRoles}
                    onChange={(event) => setTargetRoles(event.target.value)}
                    placeholder="Backend Engineer, Software Engineer"
                  />
                  <ChipPreview items={roleChips} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="locations">Target locations</Label>
                  <Input
                    id="locations"
                    value={targetLocations}
                    onChange={(event) => setTargetLocations(event.target.value)}
                    placeholder="Remote, Toronto"
                  />
                  <ChipPreview items={locationChips} />
                </div>
              </div>

              {message ? <Alert variant="success">{message}</Alert> : null}

              <Button onClick={() => void handleSave()} disabled={saving}>
                {saving ? "Saving..." : "Save profile"}
              </Button>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </AuthGuard>
  );
}
