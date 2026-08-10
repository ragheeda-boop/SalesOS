/** Canonical opportunity stages — matches backend OpportunityStage.default_pipeline. */
export type OpportunityStage =
  | "prospecting"
  | "qualification"
  | "proposal"
  | "negotiation"
  | "closed_won"
  | "closed_lost";

export type OpportunitySource = "nba" | "manual" | "import" | "signal";

export const STAGES: OpportunityStage[] = [
  "prospecting",
  "qualification",
  "proposal",
  "negotiation",
  "closed_won",
  "closed_lost",
];

export const STAGE_LABEL: Record<OpportunityStage, string> = {
  prospecting: "استكشاف",
  qualification: "تأهيل",
  proposal: "عرض سعر",
  negotiation: "تفاوض",
  closed_won: "صفقة مغلقة",
  closed_lost: "خسارة",
};

export const STAGE_WEIGHT: Record<OpportunityStage, number> = {
  prospecting: 0.10,
  qualification: 0.25,
  proposal: 0.50,
  negotiation: 0.75,
  closed_won: 1.0,
  closed_lost: 0,
};

export interface OpportunityNote {
  id: string;
  text: string;
  createdAt: string;
  author: string;
}

export interface RevenueOpportunity {
  id: string;
  companyId: string;
  companyName: string;
  title: string;
  source: OpportunitySource;
  sourceActionId?: string;
  estimatedValue: number;
  confidence: number;
  winProbability: number;
  stage: OpportunityStage;
  createdAt: string;
  expectedCloseDate?: string;
  stageChangedAt?: string;
  buyingIntent: number;
  relationshipStrength: number;
  riskLevel: "low" | "medium" | "high";
  assignee?: string;
  team?: string[];
  tags: string[];
  notes: OpportunityNote[];
  lastActivityAt?: string;
}

export function calculateWinProbability(opportunity: {
  stage: OpportunityStage;
  buyingIntent: number;
  relationshipStrength: number;
  nbaConfidence: number;
  signalActivity: number;
}): number {
  return Math.min(
    1,
    0.3 * STAGE_WEIGHT[opportunity.stage] +
      0.25 * opportunity.buyingIntent +
      0.2 * opportunity.relationshipStrength +
      0.15 * opportunity.signalActivity +
      0.1 * opportunity.nbaConfidence
  );
}
