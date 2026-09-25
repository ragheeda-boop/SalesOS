"use client";

import { AiMemoryStudio } from "@/features/tenant-studio/AiMemoryStudio";
import { AiModelTiersStudio } from "@/features/tenant-studio/AiModelTiersStudio";
import { AiPoliciesStudio } from "@/features/tenant-studio/AiPoliciesStudio";
import { PromptLibraryStudio } from "@/features/tenant-studio/PromptLibraryStudio";
import { PageHeader } from "../../_components/page-header";
import { LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";

export type AiStudioSurface = "prompts" | "policies" | "memory" | "model-tiers";

const SURFACE_CONFIG: Record<
  AiStudioSurface,
  { title: string; description: string; note: string }
> = {
  prompts: {
    title: "Prompt Library",
    description: "Review and edit reusable prompt templates for internal AI workflows.",
    note: "Prompt templates and versions are saved per tenant with row-level isolation. This page does not enable live AI providers.",
  },
  policies: {
    title: "AI Policies",
    description: "Review data-class rules and policy evaluations for AI-assisted workflows.",
    note: "Policy sets are saved per tenant with row-level isolation and evaluated deterministically. Copilot remains disabled by default.",
  },
  memory: {
    title: "AI Memory",
    description: "Inspect the opt-in conversation memory workspace.",
    note: "Conversation turns are encrypted and stored per tenant. Turning opt-in off deletes saved conversations. Cross-session recall and live model access remain disabled.",
  },
  "model-tiers": {
    title: "AI Model Tiers",
    description: "Review available model tiers and plan defaults.",
    note: "Platform admins can save each plan’s default and allowed tiers. Tenant resolution is read-only; Copilot and live model access remain disabled.",
  },
};

const SURFACE_CONTENT = {
  prompts: <PromptLibraryStudio />,
  policies: <AiPoliciesStudio />,
  memory: <AiMemoryStudio />,
  "model-tiers": <AiModelTiersStudio />,
} satisfies Record<AiStudioSurface, React.ReactNode>;

export function AiStudioWorkspace({ surface }: { surface: AiStudioSurface }) {
  const { ready, hasToken } = useAccessToken();
  const config = SURFACE_CONFIG[surface];

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath={`/v3/admin/ai-${surface}`} />;

  return (
    <div className="space-y-4">
      <PageHeader title={config.title} description={config.description} />
      <p
        role="note"
        className="rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3 text-sm text-[var(--text-secondary)]"
      >
        {config.note}
      </p>
      {SURFACE_CONTENT[surface]}
    </div>
  );
}
