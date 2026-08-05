"use client";

import {
  Card,
  CardContent,
  CardHeader,
  Skeleton,
  EmptyState,
  Badge,
} from "@salesos/ui";
import { Brain, BarChart3, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface ScoreFactor {
  name: string;
  label: string;
  contribution: number;
  weight?: number;
}

interface ScoreBreakdownProps {
  score: number;
  trend?: "up" | "down" | "stable";
  confidence?: number;
  factors: ScoreFactor[];
  isLoading?: boolean;
}

function GaugeCircle({ score, label }: { score: number; label: string }) {
  const circumference = 2 * Math.PI * 42;
  const strokeDasharray = `${(score / 100) * circumference} ${circumference}`;
  const gaugeColor =
    score >= 70
      ? "stroke-success-500"
      : score >= 40
        ? "stroke-warning-500"
        : "stroke-danger-500";

  return (
    <div className="relative">
      <svg className="h-32 w-32 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-[var(--bg-tertiary)]"
        />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className={gaugeColor}
          strokeDasharray={strokeDasharray}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-[var(--text-primary)]">
          {score}
        </span>
        <span className="text-[10px] text-[var(--text-muted)]">{label}</span>
      </div>
    </div>
  );
}

function FactorBar({
  label,
  value,
  maxValue,
}: {
  label: string;
  value: number;
  maxValue: number;
}) {
  const width = maxValue > 0 ? (value / maxValue) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-[var(--text-secondary)]">{label}</span>
        <span className="font-medium text-[var(--text-primary)]">
          +{value}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
        <div
          className="h-full rounded-full bg-[var(--muhide-orange)] transition-all duration-500"
          style={{ width: `${Math.min(100, width)}%` }}
        />
      </div>
    </div>
  );
}

export function ScoreBreakdown({
  score,
  trend,
  confidence,
  factors,
  isLoading,
}: ScoreBreakdownProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Skeleton className="h-56 rounded-xl" />
        <Skeleton className="h-56 rounded-xl md:col-span-2" />
      </div>
    );
  }

  if (factors.length === 0) {
    return (
      <div className="py-12">
        <EmptyState
          icon={<Brain className="h-10 w-10" />}
          title={t("emp360.no_score")}
          description={t("emp360.no_score_hint")}
        />
      </div>
    );
  }

  const maxContribution = Math.max(...factors.map((f) => f.contribution), 1);
  const trendIcon =
    trend === "up" ? (
      <TrendingUp className="h-4 w-4 text-success-500" />
    ) : trend === "down" ? (
      <TrendingDown className="h-4 w-4 text-danger-500" />
    ) : (
      <Minus className="h-4 w-4 text-[var(--text-disabled)]" />
    );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <Card className="flex flex-col items-center justify-center">
        <CardContent className="py-6">
          <GaugeCircle score={score} label={t("emp360.out_of_100")} />
          {trend && (
            <div className="mt-4 flex items-center justify-center gap-1.5 text-sm">
              <span className="text-[var(--text-muted)]">
                {t("emp360.trend")}:
              </span>
              {trendIcon}
              <span className="text-xs text-[var(--text-disabled)] capitalize">
                {trend}
              </span>
            </div>
          )}
          {confidence !== undefined && (
            <div className="mt-3 flex items-center gap-2 text-xs">
              <span className="text-[var(--text-muted)]">
                {t("emp360.confidence")}:
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                <div
                  className="h-full rounded-full bg-info-500"
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <span className="font-medium text-[var(--text-secondary)]">
                {Math.round(confidence)}%
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-[var(--chart-purple)]" />
            <h3 className="text-sm font-semibold">{t("emp360.factors")}</h3>
            <Badge variant="primary" className="text-[10px]">
              {factors.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {factors.map((factor) => (
              <FactorBar
                key={factor.name}
                label={factor.label}
                value={factor.contribution}
                maxValue={maxContribution}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
