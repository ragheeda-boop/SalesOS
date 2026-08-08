"use client";

import { useEmployeeScore } from "@/lib/hooks/employeeQueries";
import { useDecisionScores } from "@/lib/decisionQueries";
import { Skeleton } from "@salesos/ui";
import { useTranslation } from "@/lib/i18n";
import { ErrorFallback } from "@/components/foundation/error-boundary";
import { ScoreBreakdown } from "./employee-360-score-breakdown";
import { CoachingInsights } from "./employee-360-coaching";
import type { Score } from "@salesos/decision-platform";

export function EmployeeScoring({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation();
  const { data: decisionScores, isLoading: dpLoading } = useDecisionScores(employeeId, "employee");
  const {
    data: scoreData,
    isLoading: domainLoading,
    isError,
    error,
    refetch,
  } = useEmployeeScore(employeeId);

  const isLoading = dpLoading && domainLoading;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-56 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  if (isError && (!decisionScores || decisionScores.length === 0)) {
    return (
      <div className="py-12">
        <ErrorFallback
          title={t("emp360.score_error")}
          message={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const hasDpScores = decisionScores && decisionScores.length > 0;
  const hasDomainScore = scoreData !== null && scoreData !== undefined;

  const gaugeScore = hasDomainScore
    ? scoreData.score
    : Math.round(
        (decisionScores!.reduce(
          (sum: number, s: Score) => sum + (typeof s.value === "number" ? s.value : 0),
          0
        ) /
          decisionScores!.length) *
          100
      );

  const factors = hasDpScores
    ? decisionScores!.slice(0, 6).map((s: Score) => ({
        name: s.name,
        label: s.label || s.name,
        contribution: Math.round((typeof s.value === "number" ? s.value : 0) * 100),
      }))
    : hasDomainScore
      ? scoreData.factors.map((f) => ({
          name: f.name,
          label: f.label,
          contribution: f.contribution,
        }))
      : [];

  return (
    <div className="space-y-4">
      <ScoreBreakdown
        score={gaugeScore}
        trend={hasDomainScore ? scoreData.trend : undefined}
        confidence={hasDomainScore ? scoreData.confidence : undefined}
        factors={factors}
      />
      {hasDomainScore && factors.length > 0 && (
        <CoachingInsights score={gaugeScore} factors={factors} trend={scoreData.trend} />
      )}
    </div>
  );
}
