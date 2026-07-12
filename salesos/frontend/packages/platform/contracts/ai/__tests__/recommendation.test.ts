import type {
  SignalSource,
  SignalEntityType,
  OpportunityStage,
  RecommendationStatus,
  ConfidenceLabel,
  RecommendationSource,
  EvidenceType,
  RiskLevel,
  RiskFactorType,
  ImpactCategory,
  Evidence,
  Confidence,
  Impact,
  Risk,
  Alternative,
  Recommendation,
  PipelineTrace,
  Feedback,
} from "../recommendation"

describe("Contract: AI Recommendation", () => {
  describe("1. Type exports exist", () => {
    it("exports all union types", () => {
      const signalSource: SignalSource = "stage_change"
      const entityType: SignalEntityType = "opportunity"
      const stage: OpportunityStage = "discovery"
      const status: RecommendationStatus = "pending"
      const confidence: ConfidenceLabel = "high"
      const source: RecommendationSource = "ai"
      const evidenceType: EvidenceType = "ai_analysis"
      const risk: RiskLevel = "medium"
      const riskFactor: RiskFactorType = "engagement_drop"
      const impact: ImpactCategory = "revenue"

      expect(signalSource).toBe("stage_change")
      expect(entityType).toBe("opportunity")
      expect(stage).toBe("discovery")
      expect(status).toBe("pending")
      expect(confidence).toBe("high")
      expect(source).toBe("ai")
      expect(evidenceType).toBe("ai_analysis")
      expect(risk).toBe("medium")
      expect(riskFactor).toBe("engagement_drop")
      expect(impact).toBe("revenue")
    })
  })

  describe("2. Evidence interface", () => {
    it("is constructible with required fields", () => {
      const e: Evidence = {
        id: "e1",
        type: "signal",
        description: "Recent activity spike",
        source: "crm",
        confidence: 0.85,
        timestamp: "2026-01-01T00:00:00Z",
      }
      expect(e.id).toBe("e1")
      expect(e.type).toBe("signal")
      expect(e.confidence).toBe(0.85)
    })

    it("supports optional data field", () => {
      const e: Evidence = {
        id: "e1",
        type: "business_rule",
        description: "Rule hit",
        source: "engine",
        confidence: 1.0,
        timestamp: "2026-01-01T00:00:00Z",
        data: { key: "value" },
      }
      expect(e.data).toEqual({ key: "value" })
    })
  })

  describe("3. Confidence interface", () => {
    it("is constructible with all components", () => {
      const c: Confidence = {
        finalScore: 0.82,
        label: "high",
        components: {
          ruleScore: 0.7,
          aiScore: 0.9,
          opportunityScore: 0.8,
          urgencyScore: 0.75,
          riskAdjustment: -0.1,
        },
      }
      expect(c.label).toBe("high")
      expect(c.components.aiScore).toBe(0.9)
    })
  })

  describe("4. Impact interface", () => {
    it("is constructible", () => {
      const i: Impact = {
        description: "Revenue increase",
        estimatedRevenue: 50000,
        estimatedProbability: 0.7,
        category: "revenue",
      }
      expect(i.estimatedRevenue).toBe(50000)
    })

    it("supports optional fields", () => {
      const i: Impact = {
        description: "Build relationship",
        category: "relationship",
      }
      expect(i.estimatedRevenue).toBeUndefined()
    })
  })

  describe("5. Risk interface", () => {
    it("is constructible", () => {
      const r: Risk = {
        type: "competition",
        level: "high",
        description: "Competitor entered deal",
        detectedAt: "2026-01-01T00:00:00Z",
      }
      expect(r.level).toBe("high")
    })
  })

  describe("6. Alternative interface", () => {
    it("is constructible", () => {
      const a: Alternative = {
        action: "Send proposal",
        reason: "Prospect engaged",
        confidence: 0.75,
      }
      expect(a.action).toBe("Send proposal")
    })
  })

  describe("7. Recommendation interface", () => {
    it("is constructible with all required fields", () => {
      const r: Recommendation = {
        id: "rec-1",
        opportunityId: "opp-1",
        action: "Schedule call",
        reason: "High engagement detected",
        evidence: [],
        confidence: 0.88,
        confidenceLabel: "high",
        source: "ai",
        alternatives: [],
        expectedImpact: { description: "Revenue", category: "revenue" },
        potentialRisks: [],
        status: "pending",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-01T00:00:00Z",
      }
      expect(r.id).toBe("rec-1")
      expect(r.status).toBe("pending")
    })

    it("supports optional dueBy", () => {
      const r: Recommendation = {
        id: "rec-2",
        opportunityId: "opp-2",
        action: "Follow up",
        reason: "Stagnation risk",
        evidence: [],
        confidence: 0.6,
        confidenceLabel: "medium",
        source: "rule",
        alternatives: [],
        expectedImpact: { description: "Prevent loss", category: "risk_mitigation" },
        potentialRisks: [],
        dueBy: "2026-02-01T00:00:00Z",
        status: "accepted",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-15T00:00:00Z",
      }
      expect(r.dueBy).toBe("2026-02-01T00:00:00Z")
    })
  })

  describe("8. PipelineTrace interface", () => {
    it("is constructible", () => {
      const t: PipelineTrace = {
        normalizationMs: 5,
        rulesMs: 12,
        scoringMs: 20,
        aiMs: 150,
        riskMs: 8,
        confidenceMs: 3,
        totalMs: 198,
      }
      expect(t.totalMs).toBe(198)
    })
  })

  describe("9. Feedback interface", () => {
    it("is constructible", () => {
      const f: Feedback = {
        id: "fb-1",
        nbaId: "nba-1",
        opportunityId: "opp-1",
        userId: "u-1",
        action: "accepted",
        reason: "Good timing",
        timestamp: "2026-01-01T00:00:00Z",
      }
      expect(f.action).toBe("accepted")
    })

    it("supports optional reason", () => {
      const f: Feedback = {
        id: "fb-2",
        nbaId: "nba-2",
        opportunityId: "opp-2",
        userId: "u-2",
        action: "dismissed",
        timestamp: "2026-01-01T00:00:00Z",
      }
      expect(f.reason).toBeUndefined()
    })
  })
})
