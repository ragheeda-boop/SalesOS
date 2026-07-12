import {
  decisionEngine,
  ScoringEngine,
  FeedbackEngine,
} from "../index"
import type {
  Score,
  ScoreType,
  DecisionContext,
  DecisionResult,
  Explainability,
  DecisionHistoryItem,
  Feedback,
} from "../index"

describe("Decision Platform - index", () => {
  describe("1. All exports exist", () => {
    it("exports decisionEngine", () => {
      expect(decisionEngine).toBeDefined()
    })

    it("exports ScoringEngine class", () => {
      expect(ScoringEngine).toBeDefined()
    })

    it("exports FeedbackEngine class", () => {
      expect(FeedbackEngine).toBeDefined()
    })
  })

  describe("2. decisionEngine.evaluate", () => {
    it("exists and is callable", () => {
      expect(typeof decisionEngine.evaluate).toBe("function")
    })

    it("throws not implemented by default", async () => {
      const context: DecisionContext = {
        actorId: "user-1",
        entityType: "opportunity",
      }
      await expect(decisionEngine.evaluate(context)).rejects.toThrow("Not implemented")
    })
  })

  describe("3. decisionEngine.evaluateBatch", () => {
    it("exists and is callable", () => {
      expect(typeof decisionEngine.evaluateBatch).toBe("function")
    })

    it("throws not implemented by default", async () => {
      await expect(decisionEngine.evaluateBatch([])).rejects.toThrow("Not implemented")
    })
  })

  describe("4. decisionEngine.explain", () => {
    it("exists and is callable", () => {
      expect(typeof decisionEngine.explain).toBe("function")
    })

    it("throws not implemented by default", async () => {
      await expect(decisionEngine.explain("dec-1")).rejects.toThrow("Not implemented")
    })
  })

  describe("5. decisionEngine.getHistory", () => {
    it("exists and is callable", () => {
      expect(typeof decisionEngine.getHistory).toBe("function")
    })

    it("throws not implemented by default", async () => {
      await expect(decisionEngine.getHistory("tenant-1")).rejects.toThrow("Not implemented")
    })
  })

  describe("6. ScoringEngine", () => {
    it("instantiates", () => {
      const engine = new ScoringEngine()
      expect(engine).toBeDefined()
    })

    it("has score method", () => {
      const engine = new ScoringEngine()
      expect(typeof engine.score).toBe("function")
    })

    it("score throws not implemented by default", () => {
      const engine = new ScoringEngine()
      expect(() => engine.score("engagement", {})).toThrow("Not implemented")
    })
  })

  describe("7. FeedbackEngine", () => {
    it("instantiates", () => {
      const engine = new FeedbackEngine()
      expect(engine).toBeDefined()
    })

    it("has submit method", () => {
      const engine = new FeedbackEngine()
      expect(typeof engine.submit).toBe("function")
    })

    it("has getStats method", () => {
      const engine = new FeedbackEngine()
      expect(typeof engine.getStats).toBe("function")
    })

    it("submit throws not implemented by default", async () => {
      const engine = new FeedbackEngine()
      const feedback: Feedback = {
        id: "f1",
        decisionId: "dec-1",
        outcome: "accepted",
        createdAt: "2026-01-01T00:00:00Z",
      }
      await expect(engine.submit(feedback)).rejects.toThrow("Not implemented")
    })

    it("getStats throws not implemented by default", async () => {
      const engine = new FeedbackEngine()
      await expect(engine.getStats("tenant-1")).rejects.toThrow("Not implemented")
    })
  })

  describe("8. Type exports (compile-time validation)", () => {
    it("Score type is usable", () => {
      const score: Score = { name: "engagement", value: 0.8, label: "Engagement", weight: 0.5 }
      expect(score.name).toBe("engagement")
      expect(score.value).toBe(0.8)
    })

    it("ScoreType type is usable", () => {
      const t: ScoreType = "engagement"
      expect(t).toBe("engagement")
    })

    it("DecisionContext type is usable", () => {
      const ctx: DecisionContext = { actorId: "u1", entityType: "opportunity" }
      expect(ctx.actorId).toBe("u1")
    })

    it("DecisionResult type is usable", () => {
      const result: DecisionResult = {
        id: "r1",
        recommendation: "Follow up",
        confidence: 0.9,
        action: "call",
        reasoning: "High engagement",
        scores: [],
        explainability: { factors: [], summary: "test" },
      }
      expect(result.id).toBe("r1")
    })

    it("Explainability type is usable", () => {
      const exp: Explainability = {
        factors: [{ name: "f1", value: 0.5, description: "desc", impact: "high" }],
        summary: "test summary",
      }
      expect(exp.factors.length).toBe(1)
    })

    it("DecisionHistoryItem type is usable", () => {
      const item: DecisionHistoryItem = {
        id: "h1",
        decisionId: "dec-1",
        action: "call",
        outcome: "success",
        timestamp: "2026-01-01T00:00:00Z",
      }
      expect(item.decisionId).toBe("dec-1")
    })

    it("Feedback type is usable", () => {
      const fb: Feedback = {
        id: "f1",
        decisionId: "dec-1",
        outcome: "accepted",
        createdAt: "2026-01-01T00:00:00Z",
      }
      expect(fb.outcome).toBe("accepted")
    })
  })
})
