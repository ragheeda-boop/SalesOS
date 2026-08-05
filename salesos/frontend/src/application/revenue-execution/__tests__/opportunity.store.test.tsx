jest.mock("@/lib/api", () => {
  const store: any[] = [];
  return {
    __esModule: true,
    default: {
      get: jest.fn(() => Promise.resolve({ data: { items: store } })),
      post: jest.fn((_url: string, input: any) => {
        const opp = {
          id: "opp_" + Math.random().toString(36).slice(2, 10),
          companyId: input.company_id,
          title: input.title,
          estimatedValue: input.estimated_value,
          confidence: input.confidence,
          buyingIntent: input.buying_intent,
          relationshipStrength: input.relationship_strength,
          sourceActionId: input.source_action_id,
          stage: "identified",
          createdAt: "2026-07-11T12:00:00.000Z",
          winProbability: 0.1,
          riskLevel: input.confidence >= 0.9 ? "low" : input.confidence <= 0.4 ? "high" : "medium",
          lastActivityAt: "2026-07-11T12:00:00.000Z",
          notes: [],
          tags: [],
          source: "nba",
        };
        store.push(opp);
        return Promise.resolve({ data: opp });
      }),
      put: jest.fn((url: string, body: any) => {
        const id = url.match(/opportunities\/([^/]+)\/stage/)?.[1];
        const opp = store.find((o: any) => o.id === id);
        if (opp && body?.stage) {
          opp.stage = body.stage;
          opp.lastActivityAt = "2026-07-11T13:00:00.000Z";
        }
        return Promise.resolve({ data: { items: [...store] } });
      }),
      patch: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      __store: store,
    },
  };
});

import api from "@/lib/api";
import {
  loadOpportunities,
  createOpportunity,
  updateOpportunityStage,
  addOpportunityNote,
  getOpportunitiesByStage,
  getOpportunity,
} from "../opportunity.store";

const mockedApi = api as jest.Mocked<typeof api> & { __store: any[] };

beforeEach(() => {
  mockedApi.__store.length = 0;
  jest.clearAllMocks();
  mockedApi.get.mockImplementation(() =>
    Promise.resolve({ data: { items: mockedApi.__store } } as any)
  );
  mockedApi.post.mockImplementation((_url: string, input: any) => {
    const opp = {
      id: "opp_" + Math.random().toString(36).slice(2, 10),
      companyId: input.company_id,
      title: input.title,
      estimatedValue: input.estimated_value,
      confidence: input.confidence,
      buyingIntent: input.buying_intent,
      relationshipStrength: input.relationship_strength,
      sourceActionId: input.source_action_id,
      stage: "identified",
      createdAt: "2026-07-11T12:00:00.000Z",
      winProbability: 0.1,
      riskLevel: input.confidence >= 0.9 ? "low" : input.confidence <= 0.4 ? "high" : "medium",
      lastActivityAt: "2026-07-11T12:00:00.000Z",
      notes: [],
      tags: [],
      source: "nba",
    };
    mockedApi.__store.push(opp);
    return Promise.resolve({ data: opp } as any);
  });
  mockedApi.put.mockImplementation((url: string, body: any) => {
    const id = url.match(/opportunities\/([^/]+)\/stage/)?.[1];
    const opp = mockedApi.__store.find((o: any) => o.id === id);
    if (opp && body?.stage) {
      opp.stage = body.stage;
      opp.lastActivityAt = "2026-07-11T13:00:00.000Z";
    }
    return Promise.resolve({ data: { items: [...mockedApi.__store] } } as any);
  });
});

describe("opportunity store", () => {
  describe("loadOpportunities", () => {
    it("returns empty array when nothing stored", async () => {
      expect(await loadOpportunities()).toEqual([]);
    });
  });

  describe("createOpportunity", () => {
    it("creates an opportunity with generated id", async () => {
      const opp = await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "صفقة جديدة",
        estimatedValue: 500000,
        confidence: 0.8,
        buyingIntent: 0.7,
        relationshipStrength: 0.6,
      });

      expect(opp.id).toContain("opp_");
      expect(opp.companyId).toBe("c-1");
      expect(opp.title).toBe("صفقة جديدة");
      expect(opp.estimatedValue).toBe(500000);
      expect(opp.stage).toBe("identified");
      expect(opp.winProbability).toBe(0.1);
      expect(opp.source).toBe("nba");
      expect(opp.riskLevel).toBe("medium");
    });

    it("creates low risk for high confidence", async () => {
      const opp = await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "Test",
        estimatedValue: 100000,
        confidence: 0.9,
        buyingIntent: 0.8,
        relationshipStrength: 0.8,
      });
      expect(opp.riskLevel).toBe("low");
    });

    it("creates high risk for low confidence", async () => {
      const opp = await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "Test",
        estimatedValue: 100000,
        confidence: 0.3,
        buyingIntent: 0.8,
        relationshipStrength: 0.8,
      });
      expect(opp.riskLevel).toBe("high");
    });
  });

  describe("updateOpportunityStage", () => {
    it("updates stage and lastActivityAt", async () => {
      await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "Test",
        estimatedValue: 100000,
        confidence: 0.5,
        buyingIntent: 0.5,
        relationshipStrength: 0.5,
      });
      const all = await loadOpportunities();
      const updated = await updateOpportunityStage(all[0].id, "qualifying");

      expect(updated[0].stage).toBe("qualifying");
    });
  });

  describe("addOpportunityNote", () => {
    it("is a no-op until notes endpoint exists", async () => {
      await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "Test",
        estimatedValue: 100000,
        confidence: 0.5,
        buyingIntent: 0.5,
        relationshipStrength: 0.5,
      });
      const all = await loadOpportunities();
      const updated = await addOpportunityNote(all[0].id, "مذكرة مهمة", "أحمد");

      expect(updated).toEqual([]);
    });
  });

  describe("getOpportunitiesByStage", () => {
    it("filters by stage", async () => {
      await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "A",
        estimatedValue: 100000,
        confidence: 0.5,
        buyingIntent: 0.5,
        relationshipStrength: 0.5,
      });
      const all = await loadOpportunities();
      expect(getOpportunitiesByStage(all, "identified")).toHaveLength(1);
      expect(getOpportunitiesByStage(all, "won")).toHaveLength(0);
      expect(getOpportunitiesByStage(all)).toHaveLength(1);
    });
  });

  describe("getOpportunity", () => {
    it("finds opportunity by id", async () => {
      const created = await createOpportunity({
        companyId: "c-1",
        companyName: "شركة",
        title: "Find Me",
        estimatedValue: 100000,
        confidence: 0.5,
        buyingIntent: 0.5,
        relationshipStrength: 0.5,
      });
      const found = await getOpportunity(created.id);
      expect(found?.title).toBe("Find Me");
    });

    it("returns undefined for unknown id", async () => {
      expect(await getOpportunity("unknown")).toBeUndefined();
    });
  });
});
