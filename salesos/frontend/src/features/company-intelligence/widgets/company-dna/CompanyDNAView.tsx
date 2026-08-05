"use client";

import { cn } from "@salesos/ui";
import type { CompanyDNAViewProps } from "./types";

const TREND = { up: "↑", stable: "→", down: "↓" };
const TREND_C = {
  up: "text-[var(--color-success)] dark:text-[var(--color-success)]",
  stable: "text-[var(--color-warning)] dark:text-[var(--color-warning)]",
  down: "text-[var(--color-danger)] dark:text-[var(--color-danger)]",
};

function Gauge({
  label,
  value,
  max = 100,
  color,
}: {
  label: string;
  value: number;
  max?: number;
  color?: string;
}) {
  const pct = Math.min(100, (value / max) * 100);
  const bar =
    color ??
    (pct >= 70
      ? "bg-[var(--color-success)]"
      : pct >= 40
        ? "bg-[var(--color-warning)]"
        : "bg-[var(--color-danger)]");
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
        <span className="truncate">{label}</span>
        <span className="font-semibold text-[var(--text-primary)]">
          {value}
          {max === 100 ? "%" : ""}
        </span>
      </div>
      <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
        <div
          className={cn("h-full rounded-full transition-all", bar)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function Badge({
  label,
  variant,
}: {
  label: string;
  variant: "info" | "success" | "warning" | "danger" | "neutral";
}) {
  const v = {
    info: "bg-[var(--color-info-bg)] text-[var(--color-info)]",
    success: "bg-[var(--color-success-bg)] text-[var(--color-success)]",
    warning: "bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
    danger: "bg-[var(--color-danger-bg)] text-[var(--color-danger)]",
    neutral: "bg-[var(--color-neutral-bg)] text-[var(--color-neutral)]",
  };
  return (
    <span className={cn("rounded-full px-1.5 py-0.5 text-[9px] font-medium", v[variant])}>
      {label}
    </span>
  );
}

function MetricBox({
  label,
  value,
  trend,
}: {
  label: string;
  value: string;
  trend?: "up" | "stable" | "down";
}) {
  return (
    <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
      <p className="text-[9px] text-[var(--text-muted)]">{label}</p>
      <p className="mt-0.5 text-xs font-bold text-[var(--text-primary)]">
        {value}
        {trend && <span className={cn("mr-0.5 text-[10px]", TREND_C[trend])}>{TREND[trend]}</span>}
      </p>
    </div>
  );
}

export function CompanyDNAView({ dna }: CompanyDNAViewProps) {
  if (!dna) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">
          🧬
        </span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">جاري تحليل الشركة</p>
      </div>
    );
  }

  return (
    <div role="region" aria-label="الحمض النووي للشركة" className="space-y-2">
      {/* Row 1: Identity */}
      <div className="flex items-center gap-2">
        <Badge label={dna.industry} variant="info" />
        <Badge label={dna.businessModel} variant="neutral" />
        <Badge
          label={dna.size.label}
          variant={dna.size.label === "enterprise" ? "success" : "warning"}
        />
        {dna.growthPattern === "accelerating" && <Badge label="متسارع" variant="success" />}
      </div>

      {/* Row 2: Key Metrics */}
      <div className="grid grid-cols-3 gap-1.5">
        <MetricBox label="الموظفون" value={dna.size.employees.toLocaleString()} />
        <MetricBox
          label="الإيرادات"
          value={`$${dna.financialHealth.revenue >= 1e9 ? (dna.financialHealth.revenue / 1e9).toFixed(1) + "B" : (dna.financialHealth.revenue / 1e6).toFixed(0) + "M"}`}
        />
        <MetricBox
          label="النمو"
          value={`%${dna.financialHealth.growth}`}
          trend={dna.financialHealth.trend}
        />
      </div>

      {/* Row 3: Gauges */}
      <div className="space-y-1.5">
        <Gauge label="الصحة المالية" value={dna.financialHealth.score} />
        <Gauge label="نية الشراء" value={dna.buyingIntent.score} />
        <Gauge label="العلاقات" value={dna.relationshipStrength.score} />
        <Gauge label="النضج الشرائي" value={dna.procurementMaturity.score} />
        <Gauge label="الوجود الرقمي" value={dna.digitalPresence.score} />
        <Gauge label="التوسع المحتمل" value={dna.expansionPotential.score} />
        <Gauge label="جودة البيانات" value={dna.dataFreshness.score} />
      </div>

      {/* Row 4: Bottom bar */}
      <div className="flex items-center justify-between border-t border-[var(--border-color)] pt-1.5 text-[9px] text-[var(--text-muted)]">
        <span>ثقة: %{Math.round(dna.confidenceScore * 100)}</span>
        <span>مخاطرة: {dna.riskLevel.level}</span>
        <span>مصادر: {dna.goldenRecordStatus.sources}</span>
      </div>
    </div>
  );
}
