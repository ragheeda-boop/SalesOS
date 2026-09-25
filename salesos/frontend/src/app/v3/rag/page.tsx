"use client";

import { RagWorkspace } from "@/features/rag/workspace/rag/RagWorkspace";
import { PageHeader } from "../_components/page-header";
import { LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

export default function V3RagPage() {
  const { ready, hasToken } = useAccessToken();

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/rag" />;

  return (
    <section className="space-y-4">
      <PageHeader
        title="Knowledge workspace"
        description="Ask questions over your tenant's saved notes, emails, and meeting documents. Answers depend on the documents available to your workspace."
      />
      <RagWorkspace />
    </section>
  );
}
