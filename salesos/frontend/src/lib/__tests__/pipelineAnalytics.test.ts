import { normalizePipelineAnalytics } from "../pipelineAnalytics";

describe("normalizePipelineAnalytics", () => {
  it("maps BE velocity object to chart array without throwing", () => {
    const view = normalizePipelineAnalytics({
      velocity: {
        avg_cycle_days: 12,
        avg_days_per_stage: { lead: 3, proposal: 5 },
        fastest_close_days: 2,
        slowest_close_days: 40,
      },
      stage_durations: [{ stage: "lead", median_days: 3, max_days: 10, avg_days: 4 }],
      conversion_rates: [{ from: "lead", to: "opportunity", rate: 0.2, count: 2, total: 10 }],
      value_over_time: [{ month: "2026-01", total_value: 1000 }],
      win_loss: { win_rate: 0.5, total_won: 2, total_lost: 2 },
      total_pipeline_value: 50000,
      overall_conversion_rate: 0.1,
      active_deals: 5,
    });

    expect(view.velocity).toEqual([
      { stage: "lead", avg_days: 3 },
      { stage: "proposal", avg_days: 5 },
    ]);
    expect(view.avg_cycle_days).toBe(12);
    expect(view.win_rate).toBe(50);
    expect(view.total_pipeline).toBe(50000);
    expect(view.stage_duration[0].p50).toBe(3);
    expect(view.value_over_time[0].value).toBe(1000);
  });

  it("tolerates empty / null payloads", () => {
    const view = normalizePipelineAnalytics(null);
    expect(view.velocity).toEqual([]);
    expect(view.total_pipeline).toBe(0);
    expect(view.win_rate).toBe(0);
  });
});
