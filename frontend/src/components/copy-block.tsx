"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

export function CopyBlock({ content, label = "Copy" }: { content: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="relative rounded-lg border border-zinc-800 bg-zinc-950/80">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">Output</span>
        <Button variant="ghost" size="sm" onClick={() => void handleCopy()}>
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : label}
        </Button>
      </div>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap p-4 text-sm leading-relaxed text-zinc-300">
        {content}
      </pre>
    </div>
  );
}
