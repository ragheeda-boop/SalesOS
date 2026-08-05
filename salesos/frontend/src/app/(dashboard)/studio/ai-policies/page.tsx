"use client";

import Link from "next/link";
import { AiPoliciesStudio } from "@/features/tenant-studio/AiPoliciesStudio";

/**
 * FE-S12-02 — AI Policies Studio (tip STORY-12-02).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 */
export default function AiPoliciesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="ai-policies-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">AI Policies</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip CRUD + evaluate against /api/v1/studio/ai-policies. In-memory CAP-091 reusing AI-GR-*.
          Live LLM not claimed.
        </p>
      </div>
      <AiPoliciesStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/studio/prompt-library" className="underline">
          /studio/prompt-library
        </Link>
        {" · "}
        <Link href="/studio/ai-model-tiers" className="underline">
          /studio/ai-model-tiers
        </Link>
        .
      </p>
    </div>
  );
}
