import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

export type FactDecision = "approve" | "reject" | "dismiss";
export type FactProposalStatus =
  | "PROPOSED"
  | "APPROVED"
  | "REJECTED"
  | "DISMISSED"
  | "APPLIED"
  | "SUPERSEDED"
  | "STALE";

export type FactEvidenceSnapshot = {
  id?: string;
  evidence_kind?: string;
  evidence_type?: string;
  description?: string | null;
  confidence?: number;
  source?: {
    source_domain?: string;
    source_type?: string;
    source_name?: string | null;
    source_id?: string | null;
  };
};

export type FactProposal = {
  id: string;
  subject_type: "company" | "contact";
  subject_id: string;
  field_name: string;
  proposed_value: unknown;
  status: FactProposalStatus;
  evidence_band: string;
  score: number;
  decision_reason: string;
  actor_type: string;
  actor_id: string | null;
  evidence_snapshot: FactEvidenceSnapshot[];
  created_at: string | null;
  reviewer_id: string | null;
  reviewed_at: string | null;
};

export type FactProposalPage = {
  items: FactProposal[];
  limit: number;
  offset: number;
};

const tenantConfig = () => ({ headers: { "X-Tenant-Id": getTenantId() } });

export async function fetchFactProposals(params: {
  status: FactProposalStatus;
  limit: number;
  offset: number;
}): Promise<FactProposalPage> {
  const response = await apiClient.get<FactProposalPage>("/api/v1/facts/proposals", {
    params,
    ...tenantConfig(),
  });
  return response.data;
}

export async function decideFactProposal(input: {
  id: string;
  decision: FactDecision;
  reason: string;
}): Promise<{ id: string; status: FactProposalStatus; reviewed_at: string; changed: boolean; crm_applied: false }> {
  const response = await apiClient.post(
    `/api/v1/facts/${encodeURIComponent(input.id)}/decision`,
    { decision: input.decision, reason: input.reason },
    tenantConfig(),
  );
  return response.data;
}
