"use client";

import Link from "next/link";
import { WorkflowStudio } from "@/features/tenant-studio/WorkflowStudio";

/**
 * FE-S10-03 — Tenant Studio Workflow Builder (tip STORY-10-03).
 * Canvas → WorkflowEngine. Not Production GO / RAG GO.
 */
export default function WorkflowStudioPage() {
  return (
    <div className="space-y-6 p-6" data-testid="workflow-studio-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Workflow Builder Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Author canvas graphs that compile to the existing Workflow Engine. Loops / for_each are
          deferred on tip.
        </p>
      </div>
      <WorkflowStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/studio/permissions"
          className="underline"
          data-testid="workflow-permissions-link"
        >
          /studio/permissions
        </Link>
        .
      </p>
    </div>
  );
}
