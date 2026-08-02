"use client";

import Link from "next/link";
import { AiModelTiersStudio } from "@/features/tenant-studio/AiModelTiersStudio";

/**
 * FE-S12-04 — AI model tier Studio (tip STORY-12-04 GET-only).
 * feature_ai_copilot stays False. Not Production GO / RAG GO.
 */
export default function AiModelTiersPage() {
  return (
    <div className="space-y-6 p-6" data-testid="ai-model-tiers-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          AI Model Tiers
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Read-only tip /api/v1/studio/ai-model-tiers catalog, plan defaults,
          and tenant resolve. Does not enable feature_ai_copilot or live LLM.
        </p>
      </div>
      <AiModelTiersStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/studio/territories"
          className="underline"
          data-testid="ai-model-tiers-territories-link"
        >
          /studio/territories
        </Link>
        .
      </p>
    </div>
  );
}
