import api from "@/lib/api";
import {
  STAGES,
  STAGE_WEIGHT,
  type OpportunityNote,
  type OpportunitySource,
  type RevenueOpportunity,
  type OpportunityStage,
} from "./opportunity.dto";

type OpportunityApiRecord = {
  id: string;
  name?: string | null;
  title?: string | null;
  stage?: string | null;
  value?: number | null;
  estimatedValue?: number | null;
  company_id?: string | null;
  companyId?: string | null;
  company_name?: string | null;
  companyName?: string | null;
  source?: string | null;
  sourceActionId?: string | null;
  source_action_id?: string | null;
  confidence?: number | null;
  probability?: number | null;
  winProbability?: number | null;
  buyingIntent?: number | null;
  relationshipStrength?: number | null;
  created_at?: string | null;
  createdAt?: string | null;
  tags?: string[] | null;
  notes?: RevenueOpportunity["notes"] | null;
};

function normalizeStage(value: unknown): OpportunityStage {
  return STAGES.find((stage) => stage === value) ?? "prospecting";
}

function normalizeSource(value: unknown): OpportunitySource {
  return value === "nba" || value === "manual" || value === "import" || value === "signal"
    ? value
    : "unknown";
}

function toRevenueOpportunity(
  record: OpportunityApiRecord,
  fallback: Partial<RevenueOpportunity> = {}
): RevenueOpportunity {
  const stage = normalizeStage(record.stage ?? fallback.stage);
  const confidence = record.confidence ?? fallback.confidence ?? 0;
  const createdAt = record.created_at ?? record.createdAt ?? fallback.createdAt ?? "";
  const source = normalizeSource(record.source ?? fallback.source);

  return {
    id: record.id,
    companyId: record.company_id ?? record.companyId ?? fallback.companyId ?? "",
    companyName:
      record.company_name ??
      record.companyName ??
      fallback.companyName ??
      record.company_id ??
      record.companyId ??
      fallback.companyId ??
      "",
    title: record.name ?? record.title ?? fallback.title ?? "",
    source,
    sourceActionId: record.source_action_id ?? record.sourceActionId ?? fallback.sourceActionId,
    estimatedValue: record.value ?? record.estimatedValue ?? fallback.estimatedValue ?? 0,
    confidence,
    winProbability:
      record.probability ?? record.winProbability ?? fallback.winProbability ?? STAGE_WEIGHT[stage],
    stage,
    createdAt,
    expectedCloseDate: fallback.expectedCloseDate,
    stageChangedAt: fallback.stageChangedAt,
    buyingIntent: record.buyingIntent ?? fallback.buyingIntent ?? 0,
    relationshipStrength: record.relationshipStrength ?? fallback.relationshipStrength ?? 0,
    riskLevel: confidence >= 0.9 ? "low" : confidence <= 0.4 ? "high" : "medium",
    assignee: fallback.assignee,
    team: fallback.team,
    tags: record.tags ?? fallback.tags ?? [],
    notes: record.notes ?? fallback.notes ?? [],
    lastActivityAt: fallback.lastActivityAt ?? createdAt,
  };
}

export async function loadOpportunities(): Promise<RevenueOpportunity[]> {
  try {
    const response = await api.get("/api/v1/opportunities");
    const payload = response.data;
    const records = payload?.items ?? payload;
    return Array.isArray(records)
      ? records.map((record: OpportunityApiRecord) => toRevenueOpportunity(record))
      : [];
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
  const response = await api.post("/api/v1/opportunities", null, {
    params: {
      company_id: input.companyId,
      name: input.title,
      value: input.estimatedValue,
    },
  });
  return toRevenueOpportunity(response.data as OpportunityApiRecord, {
    companyId: input.companyId,
    companyName: input.companyName,
    title: input.title,
    source: "nba",
    sourceActionId: input.sourceActionId,
    estimatedValue: input.estimatedValue,
    confidence: input.confidence,
    buyingIntent: input.buyingIntent,
    relationshipStrength: input.relationshipStrength,
    riskLevel: input.confidence >= 0.9 ? "low" : input.confidence <= 0.4 ? "high" : "medium",
  });
}

export async function updateOpportunityStage(
  id: string,
  stage: OpportunityStage
): Promise<RevenueOpportunity[]> {
  await api.put(`/api/v1/opportunities/${id}/stage`, {
    stage,
  });
  return loadOpportunities();
}

export async function addOpportunityNote(
  id: string,
  text: string,
  _author: string
): Promise<RevenueOpportunity[]> {
  await api.post(`/api/v1/opportunities/${id}/notes`, { text });
  const [opportunities, notes] = await Promise.all([
    loadOpportunities(),
    getOpportunityNotes(id),
  ]);
  return opportunities.map((opportunity) =>
    opportunity.id === id ? { ...opportunity, notes } : opportunity
  );
}

export async function getOpportunityNotes(id: string): Promise<OpportunityNote[]> {
  const response = await api.get(`/api/v1/opportunities/${id}/notes`);
  const records = response.data?.items ?? [];
  if (!Array.isArray(records)) return [];
  return records.map((note) => ({
    id: String(note.id),
    text: String(note.text ?? ""),
    author: String(note.author_id ?? ""),
    createdAt: String(note.created_at ?? ""),
  }));
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
