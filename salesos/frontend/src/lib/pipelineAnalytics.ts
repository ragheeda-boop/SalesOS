/**
 * Normalize GET /api/v1/pipeline/analytics payload to the chart-friendly
 * shape used by Pipeline Analytics pages. BE returns nested objects; FE
 * historically expected flat arrays — mismatch caused velocity.map crashes.
 */

export interface PipelineAnalyticsView {
  conversion_funnel: { stage: string; count: number; value: number }[];
  velocity: { stage: string; avg_days: number }[];
  stage_duration: { stage: string; p50: number; p95: number }[];
  value_over_time: { date: string; label: string; value: number }[];
  win_rate: number;
  avg_deal_size: number;
  avg_cycle_days: number;
  total_pipeline: number;
  conversion_rate_lead_to_close: number;
  total_won: number;
  total_lost: number;
}

function asNumber(v: unknown, fallback = 0): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
}

function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

export function normalizePipelineAnalytics(raw: unknown): PipelineAnalyticsView {
  const data = asRecord(raw);
  const velocityObj = asRecord(data.velocity);
  const winLoss = asRecord(data.win_loss);
  const avgDaysPerStage = asRecord(velocityObj.avg_days_per_stage);

  const velocityFromObject = Object.entries(avgDaysPerStage).map(([stage, avg]) => ({
    stage,
    avg_days: asNumber(avg),
  }));

  // Legacy FE array shape (if a proxy ever returns it)
  const velocityLegacy = asArray(data.velocity)
    .map((item) => {
      const row = asRecord(item);
      if (typeof row.stage !== "string") return null;
      return {
        stage: row.stage,
        avg_days: asNumber(row.avg_days ?? row.avg),
      };
    })
    .filter((r): r is { stage: string; avg_days: number } => r != null);

  const velocity = velocityFromObject.length > 0 ? velocityFromObject : velocityLegacy;

  const stageDurations = asArray(data.stage_durations ?? data.stage_duration).map((item) => {
    const row = asRecord(item);
    return {
      stage: String(row.stage ?? ""),
      p50: asNumber(row.median_days ?? row.p50 ?? row.avg_days),
      p95: asNumber(row.max_days ?? row.p95 ?? row.median_days ?? row.p50),
    };
  });

  const conversionFunnel = asArray(data.conversion_funnel ?? data.conversion_rates).map((item) => {
    const row = asRecord(item);
    const stage = String(row.stage ?? row.to ?? row.from ?? "");
    return {
      stage,
      count: asNumber(row.count ?? row.total),
      value: asNumber(row.value),
    };
  });

  const valueOverTime = asArray(data.value_over_time).map((item) => {
    const row = asRecord(item);
    const label = String(row.month ?? row.date ?? row.label ?? "");
    return {
      date: label,
      label,
      value: asNumber(row.total_value ?? row.value),
    };
  });

  const totalPipeline = asNumber(data.total_pipeline_value ?? data.total_pipeline);
  const winRatePct = asNumber(winLoss.win_rate ?? data.win_rate);
  // BE stores win_rate as 0–1; FE historically showed percent
  const winRate = winRatePct <= 1 ? Math.round(winRatePct * 1000) / 10 : winRatePct;
  const overallConversion = asNumber(
    data.overall_conversion_rate ?? data.conversion_rate_lead_to_close
  );
  const conversionPct =
    overallConversion <= 1 ? Math.round(overallConversion * 1000) / 10 : overallConversion;

  const activeDeals = asNumber(data.active_deals);
  const avgDealSize = asNumber(
    data.avg_deal_size,
    activeDeals > 0 ? totalPipeline / activeDeals : 0
  );

  return {
    conversion_funnel: conversionFunnel,
    velocity,
    stage_duration: stageDurations,
    value_over_time: valueOverTime,
    win_rate: winRate,
    avg_deal_size: Math.round(avgDealSize * 100) / 100,
    avg_cycle_days: asNumber(velocityObj.avg_cycle_days ?? data.avg_cycle_days),
    total_pipeline: totalPipeline,
    conversion_rate_lead_to_close: conversionPct,
    total_won: asNumber(winLoss.total_won),
    total_lost: asNumber(winLoss.total_lost),
  };
}
