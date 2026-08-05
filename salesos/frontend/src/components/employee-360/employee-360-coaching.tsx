"use client";

import { Card, CardContent, CardHeader, Badge } from "@salesos/ui";
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface CoachingInsight {
  type: "strength" | "improvement" | "warning" | "recommendation";
  title: string;
  description: string;
  factor?: string;
  impact?: "high" | "medium" | "low";
}

interface CoachingInsightsProps {
  score: number;
  factors: Array<{
    name: string;
    label: string;
    contribution: number;
  }>;
  trend?: "up" | "down" | "stable";
}

function generateInsights(
  score: number,
  factors: Array<{ name: string; label: string; contribution: number }>,
  trend?: "up" | "down" | "stable"
): CoachingInsight[] {
  const insights: CoachingInsight[] = [];

  if (score >= 70) {
    insights.push({
      type: "strength",
      title: "Strong Performance",
      description:
        "Employee is performing above average. Consider recognition or leadership opportunities.",
      impact: "high",
    });
  } else if (score < 40) {
    insights.push({
      type: "warning",
      title: "Performance Alert",
      description: "Score is below threshold. Schedule a check-in to discuss challenges.",
      impact: "high",
    });
  }

  if (trend === "down") {
    insights.push({
      type: "improvement",
      title: "Declining Trend",
      description: "Score has been decreasing. Investigate recent changes or blockers.",
      impact: "high",
    });
  } else if (trend === "up") {
    insights.push({
      type: "strength",
      title: "Positive Momentum",
      description: "Score is improving. Continue current approach and reinforce good habits.",
      impact: "medium",
    });
  }

  const sortedFactors = [...factors].sort((a, b) => b.contribution - a.contribution);
  if (sortedFactors.length > 0) {
    const topFactor = sortedFactors[0];
    insights.push({
      type: "recommendation",
      title: `Focus on ${topFactor.label}`,
      description: `This factor has the highest impact (+${topFactor.contribution}). Invest time here for maximum improvement.`,
      factor: topFactor.name,
      impact: "high",
    });
  }

  if (sortedFactors.length > 1) {
    const lowestFactor = sortedFactors[sortedFactors.length - 1];
    if (lowestFactor.contribution < 5) {
      insights.push({
        type: "warning",
        title: `Low ${lowestFactor.label}`,
        description: `Contribution is minimal (+${lowestFactor.contribution}). Consider training or support.`,
        factor: lowestFactor.name,
        impact: "medium",
      });
    }
  }

  return insights;
}

function InsightIcon({ type }: { type: CoachingInsight["type"] }) {
  switch (type) {
    case "strength":
      return <CheckCircle className="h-4 w-4 text-success-600" />;
    case "improvement":
      return <TrendingUp className="h-4 w-4 text-info-600" />;
    case "warning":
      return <AlertTriangle className="h-4 w-4 text-warning-600" />;
    case "recommendation":
      return <Lightbulb className="h-4 w-4 text-[var(--chart-purple)]" />;
  }
}

function InsightBadge({ type }: { type: CoachingInsight["type"] }) {
  const variants = {
    strength: "success" as const,
    improvement: "default" as const,
    warning: "warning" as const,
    recommendation: "primary" as const,
  };

  return (
    <Badge variant={variants[type]} className="text-[10px]">
      {type}
    </Badge>
  );
}

export function CoachingInsights({ score, factors, trend }: CoachingInsightsProps) {
  const { t } = useTranslation();
  const insights = generateInsights(score, factors, trend);

  if (insights.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-[var(--muhide-orange)]" />
          <h3 className="text-sm font-semibold">{t("emp360.coaching_insights")}</h3>
          <Badge variant="default" className="text-[10px]">
            {insights.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-3"
            >
              <InsightIcon type={insight.type} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    {insight.title}
                  </span>
                  <InsightBadge type={insight.type} />
                  {insight.impact && (
                    <Badge variant="default" className="text-[10px]">
                      {insight.impact} impact
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">{insight.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
