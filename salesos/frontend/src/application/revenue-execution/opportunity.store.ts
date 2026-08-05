import api from "@/lib/api";
import type { RevenueOpportunity, OpportunityStage } from "./opportunity.dto";

export async function loadOpportunities(): Promise<RevenueOpportunity[]> {
  try {
    const response = await api.get("/api/v1/opportunities");
    return response.data.items ?? response.data ?? [];
  } catch {
    return [];
  }
}

export async function saveOpportunities(_opps: RevenueOpportunity[]): Promise<void> {
  // Batch update not supported by backend — individual updates via updateOpportunityStage
}

export async function createOpportunity(input: {
  companyId: string;
  companyName: string;
  title: string;
  estimatedValue: number;
  confidence: number;
  buyingIntent: number;
  relationshipStrength: number;
  sourceActionId?: string;
}): Promise<RevenueOpportunity> {
  const response = await api.post("/api/v1/opportunities", {
    company_id: input.companyId,
    title: input.title,
    estimated_value: input.estimatedValue,
    confidence: input.confidence,
    buying_intent: input.buyingIntent,
    relationship_strength: input.relationshipStrength,
    source_action_id: input.sourceActionId,
  });
  return response.data;
}

export async function updateOpportunityStage(
  id: string,
  stage: OpportunityStage
): Promise<RevenueOpportunity[]> {
  const response = await api.put(`/api/v1/opportunities/${id}/stage`, {
    stage,
  });
  return response.data.items ?? [response.data];
}

export async function addOpportunityNote(
  _id: string,
  _text: string,
  _author: string
): Promise<RevenueOpportunity[]> {
  // Notes endpoint not implemented in backend — no-op
  return [];
}

export function getOpportunitiesByStage(
  opps: RevenueOpportunity[],
  stage?: OpportunityStage
): RevenueOpportunity[] {
  if (!stage) return opps;
  return opps.filter((o) => o.stage === stage);
}

export async function getOpportunity(id: string): Promise<RevenueOpportunity | undefined> {
  const opps = await loadOpportunities();
  return opps.find((o) => o.id === id);
}
