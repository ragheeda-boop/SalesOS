"use client";

import Link from "next/link";
import { AiMemoryStudio } from "@/features/tenant-studio/AiMemoryStudio";

/**
 * FE-S12-03 — AI Memory Studio (tip STORY-12-03).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 * Decision package remains STUB.
 */
export default function AiMemoryPage() {
  return (
    <div className="space-y-6 p-6" data-testid="ai-memory-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          AI Memory
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip conversation-level memory against /api/v1/studio/ai-memory.
          In-memory CAP-063; opt-in; cross-session deferred. Live LLM not
          claimed.
        </p>
      </div>
      <AiMemoryStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/studio/ai-policies" className="underline">
          /studio/ai-policies
        </Link>
        {" · "}
        <Link href="/studio/prompt-library" className="underline">
          /studio/prompt-library
        </Link>
        .
      </p>
    </div>
  );
}
