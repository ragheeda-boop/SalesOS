import { calculateWinProbability, STAGE_WEIGHT, STAGE_LABEL } from "../opportunity.dto";

describe("STAGE_WEIGHT", () => {
  it("has correct weights", () => {
    expect(STAGE_WEIGHT.prospecting).toBe(0.1);
    expect(STAGE_WEIGHT.qualification).toBe(0.25);
    expect(STAGE_WEIGHT.proposal).toBe(0.5);
    expect(STAGE_WEIGHT.negotiation).toBe(0.75);
    expect(STAGE_WEIGHT.closed_won).toBe(1.0);
    expect(STAGE_WEIGHT.closed_lost).toBe(0);
  });
});

describe("STAGE_LABEL", () => {
  it("has Arabic labels for all stages", () => {
    expect(STAGE_LABEL.prospecting).toBe("استكشاف");
    expect(STAGE_LABEL.closed_won).toBe("صفقة مغلقة");
    expect(STAGE_LABEL.closed_lost).toBe("خسارة");
  });
});

describe("calculateWinProbability", () => {
  it("returns 1 for max values", () => {
    const prob = calculateWinProbability({
      stage: "closed_won",
      buyingIntent: 1,
      relationshipStrength: 1,
      nbaConfidence: 1,
      signalActivity: 1,
    });
    expect(prob).toBe(1);
  });

  it("returns 0.30 * stage weight for zero factors", () => {
    const prob = calculateWinProbability({
      stage: "prospecting",
      buyingIntent: 0,
      relationshipStrength: 0,
      nbaConfidence: 0,
      signalActivity: 0,
    });
    expect(prob).toBeCloseTo(0.3 * 0.1, 5);
  });

  it("increases probability with higher buying intent", () => {
    const low = calculateWinProbability({
      stage: "qualification",
      buyingIntent: 0.2,
      relationshipStrength: 0.5,
      nbaConfidence: 0.5,
      signalActivity: 0.5,
    });
    const high = calculateWinProbability({
      stage: "qualification",
      buyingIntent: 0.9,
      relationshipStrength: 0.5,
      nbaConfidence: 0.5,
      signalActivity: 0.5,
    });
    expect(high).toBeGreaterThan(low);
  });

  it("scales with stage progression", () => {
    const early = calculateWinProbability({
      stage: "prospecting",
      buyingIntent: 0.5,
      relationshipStrength: 0.5,
      nbaConfidence: 0.5,
      signalActivity: 0.5,
    });
    const late = calculateWinProbability({
      stage: "negotiation",
      buyingIntent: 0.5,
      relationshipStrength: 0.5,
      nbaConfidence: 0.5,
      signalActivity: 0.5,
    });
    expect(late).toBeGreaterThan(early);
  });
});
