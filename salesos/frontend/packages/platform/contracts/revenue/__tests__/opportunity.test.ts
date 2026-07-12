import type {
  OpportunityStage,
  OpportunityHealth,
  Opportunity,
  StageMetrics,
  PipelineSummary,
  HealthMapItem,
  HealthMap,
} from "../opportunity"

describe("Contract: Revenue Opportunity", () => {
  describe("1. Type exports exist", () => {
    it("exports OpportunityStage values", () => {
      const s: OpportunityStage = "qualification"
      expect(s).toBe("qualification")
    })

    it("exports OpportunityHealth values", () => {
      const h: OpportunityHealth = "at_risk"
      expect(h).toBe("at_risk")
    })
  })

  describe("2. Opportunity interface", () => {
    it("is constructible with required fields", () => {
      const o: Opportunity = {
        id: "opp-1",
        companyId: "comp-1",
        name: "Acme Deal",
        stage: "discovery",
        value: 100000,
        currency: "SAR",
        probability: 0.6,
        health: "healthy",
        ownerId: "user-1",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-15T00:00:00Z",
      }
      expect(o.id).toBe("opp-1")
      expect(o.stage).toBe("discovery")
      expect(o.value).toBe(100000)
    })

    it("supports optional expectedCloseDate", () => {
      const o: Opportunity = {
        id: "opp-2",
        companyId: "comp-2",
        name: "Beta Deal",
        stage: "proposal",
        value: 50000,
        currency: "SAR",
        probability: 0.75,
        health: "at_risk",
        ownerId: "user-2",
        expectedCloseDate: "2026-06-01T00:00:00Z",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-15T00:00:00Z",
      }
      expect(o.expectedCloseDate).toBe("2026-06-01T00:00:00Z")
    })

    it("supports optional playbookId", () => {
      const o: Opportunity = {
        id: "opp-3",
        companyId: "comp-3",
        name: "Gamma Deal",
        stage: "negotiation",
        value: 200000,
        currency: "SAR",
        probability: 0.9,
        health: "critical",
        ownerId: "user-3",
        playbookId: "pb-1",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-15T00:00:00Z",
      }
      expect(o.playbookId).toBe("pb-1")
    })

    it("supports optional nba recommendation", () => {
      const o: Opportunity = {
        id: "opp-4",
        companyId: "comp-4",
        name: "Delta Deal",
        stage: "qualification",
        value: 75000,
        currency: "SAR",
        probability: 0.3,
        health: "healthy",
        ownerId: "user-4",
        nba: {
          id: "rec-1",
          opportunityId: "opp-4",
          action: "Schedule call",
          reason: "High interest",
          evidence: [],
          confidence: 0.85,
          confidenceLabel: "high",
          source: "ai",
          alternatives: [],
          expectedImpact: { description: "Revenue", category: "revenue" },
          potentialRisks: [],
          status: "pending",
          createdAt: "2026-01-01T00:00:00Z",
          updatedAt: "2026-01-01T00:00:00Z",
        },
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-15T00:00:00Z",
      }
      expect(o.nba).toBeDefined()
      expect(o.nba!.action).toBe("Schedule call")
    })
  })

  describe("3. StageMetrics interface", () => {
    it("is constructible", () => {
      const m: StageMetrics = {
        count: 10,
        value: 500000,
        conversionRate: 0.4,
      }
      expect(m.count).toBe(10)
      expect(m.conversionRate).toBe(0.4)
    })
  })

  describe("4. PipelineSummary interface", () => {
    it("is constructible", () => {
      const s: PipelineSummary = {
        totalValue: 1000000,
        weightedValue: 600000,
        totalCount: 20,
        byStage: {
          discovery: { count: 8, value: 300000, conversionRate: 0.5 },
          proposal: { count: 5, value: 400000, conversionRate: 0.6 },
        },
        winRate: 0.35,
        avgDealSize: 50000,
        velocityDays: 45,
      }
      expect(s.totalCount).toBe(20)
      expect(s.byStage.discovery.count).toBe(8)
    })
  })

  describe("5. HealthMapItem interface", () => {
    it("is constructible", () => {
      const h: HealthMapItem = {
        opportunityId: "opp-1",
        name: "Deal Alpha",
        health: "healthy",
        owner: "user-1",
        value: 80000,
        stage: "proposal",
      }
      expect(h.health).toBe("healthy")
    })
  })

  describe("6. HealthMap interface", () => {
    it("is constructible", () => {
      const hm: HealthMap = {
        healthy: 12,
        atRisk: 5,
        critical: 2,
        opportunities: [
          {
            opportunityId: "opp-1",
            name: "Deal One",
            health: "healthy",
            owner: "user-1",
            value: 100000,
            stage: "discovery",
          },
        ],
      }
      expect(hm.healthy).toBe(12)
      expect(hm.opportunities.length).toBe(1)
    })

    it("supports empty opportunities", () => {
      const hm: HealthMap = {
        healthy: 0,
        atRisk: 0,
        critical: 0,
        opportunities: [],
      }
      expect(hm.opportunities.length).toBe(0)
    })
  })

  describe("7. OpportunityStage exhaustive values", () => {
    it("includes all stages", () => {
      const stages: OpportunityStage[] = [
        "qualification",
        "discovery",
        "proposal",
        "negotiation",
        "closed_won",
        "closed_lost",
      ]
      expect(stages.length).toBe(6)
    })
  })

  describe("8. OpportunityHealth exhaustive values", () => {
    it("includes all health levels", () => {
      const levels: OpportunityHealth[] = ["healthy", "at_risk", "critical"]
      expect(levels.length).toBe(3)
    })
  })
})
