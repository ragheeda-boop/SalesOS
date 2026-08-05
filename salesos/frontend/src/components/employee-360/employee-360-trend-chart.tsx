"use client";

import { Card, CardContent, CardHeader, Skeleton, EmptyState } from "@salesos/ui";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface TrendPoint {
  date: string;
  score: number;
}

interface TrendChartProps {
  data: TrendPoint[];
  direction?: "up" | "down" | "stable";
  height?: number;
  isLoading?: boolean;
}

export function TrendChart({ data, direction, height = 200, isLoading }: TrendChartProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <Skeleton className="h-64 rounded-xl" />;
  }

  if (data.length === 0) {
    return (
      <div className="py-8">
        <EmptyState icon={<TrendingUp className="h-8 w-8" />} title={t("emp360.no_trend_data")} />
      </div>
    );
  }

  const maxScore = Math.max(...data.map((p) => p.score), 100);
  const minScore = Math.min(...data.map((p) => p.score), 0);
  const range = maxScore - minScore || 1;

  const points = data.map((p, i) => ({
    x: (i / Math.max(1, data.length - 1)) * 100,
    y: 100 - ((p.score - minScore) / range) * 80 - 10,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  const areaD = `${pathD} L 100 90 L 0 90 Z`;

  const trendIcon =
    direction === "up" ? (
      <TrendingUp className="h-4 w-4 text-success-500" />
    ) : direction === "down" ? (
      <TrendingDown className="h-4 w-4 text-danger-500" />
    ) : (
      <Minus className="h-4 w-4 text-[var(--text-disabled)]" />
    );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-success-600" />
            <h3 className="text-sm font-semibold">{t("emp360.score_trend")}</h3>
          </div>
          {direction && (
            <div className="flex items-center gap-1 text-sm">
              {trendIcon}
              <span className="text-xs text-[var(--text-disabled)] capitalize">{direction}</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative" style={{ height }}>
          <svg className="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <linearGradient id="trend-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="var(--muhide-orange)" stopOpacity="0.3" />
                <stop offset="100%" stopColor="var(--muhide-orange)" stopOpacity="0.02" />
              </linearGradient>
            </defs>
            <path d={areaD} fill="url(#trend-gradient)" />
            <path
              d={pathD}
              fill="none"
              stroke="var(--muhide-orange)"
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {points.map((p, i) => (
              <circle key={i} cx={p.x} cy={p.y} r="0.8" fill="var(--muhide-orange)" />
            ))}
          </svg>
          <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-[var(--text-disabled)]">
            <span>{data[0]?.date}</span>
            <span>{data[data.length - 1]?.date}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
