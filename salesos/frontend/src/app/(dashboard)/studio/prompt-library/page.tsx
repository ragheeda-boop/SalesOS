"use client";

import Link from "next/link";
import { PromptLibraryStudio } from "@/features/tenant-studio/PromptLibraryStudio";

/**
 * FE-S12-01 — Prompt Library Studio (tip STORY-12-01).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 */
export default function PromptLibraryPage() {
  return (
    <div className="space-y-6 p-6" data-testid="prompt-library-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Prompt Library
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip CRUD + versioning + rollback against
          /api/v1/studio/prompt-library. In-memory CAP-089. Live LLM not
          claimed.
        </p>
      </div>
      <PromptLibraryStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/studio/ai-model-tiers" className="underline">
          /studio/ai-model-tiers
        </Link>
        .
      </p>
    </div>
  );
}
