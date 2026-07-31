"use client";

import { useEmployeeSignals } from "@/lib/hooks/employeeQueries";
import {
  Card,
  CardContent,
  CardHeader,
  Skeleton,
  EmptyState,
} from "@salesos/ui";
import { Activity, BarChart3, TrendingUp } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { ErrorFallback } from "@/components/foundation/error-boundary";

export function EmployeeSignals({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation();
  const {
    data: signals,
    isLoading,
    isError,
    error,
    refetch,
  } = useEmployeeSignals(employeeId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-48 rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback
          title={t("emp360.signals_error")}
          message={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!signals || signals.total === 0) {
    return (
      <div className="py-12">
        <EmptyState
          icon={<Activity className="h-10 w-10" />}
          title={t("emp360.no_signals")}
          description={t("emp360.no_signals_hint")}
        />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-info-600" />
            <h3 className="text-sm font-semibold">
              {t("emp360.signals_by_type")}
            </h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.by_type.map((s) => (
              <div key={s.type} className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">
                  {s.label}
                </span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                    <div
                      className="h-full rounded-full bg-info-500"
                      style={{
                        width: `${Math.min(100, (s.count / signals.total) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-[var(--text-primary)] w-6 text-right">
                    {s.count}
                  </span>
                </div>
              </div>
            ))}
            {signals.by_type.length === 0 && (
              <p className="text-xs text-[var(--text-disabled)]">
                {t("emp360.no_data")}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-[var(--chart-purple)]" />
            <h3 className="text-sm font-semibold">
              {t("emp360.signals_by_source")}
            </h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.by_source.map((s) => (
              <div key={s.source} className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">
                  {s.label}
                </span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                    <div
                      className="h-full rounded-full bg-[var(--chart-purple)]"
                      style={{
                        width: `${Math.min(100, (s.count / signals.total) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-[var(--text-primary)] w-6 text-right">
                    {s.count}
                  </span>
                </div>
              </div>
            ))}
            {signals.by_source.length === 0 && (
              <p className="text-xs text-[var(--text-disabled)]">
                {t("emp360.no_data")}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-success-600" />
            <h3 className="text-sm font-semibold">
              {t("emp360.signals_trend")}
            </h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.trend.map((p) => (
              <div
                key={p.date}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-[var(--text-muted)]">{p.date}</span>
                <div className="flex items-center gap-1">
                  <div
                    className="h-2 rounded-full bg-[var(--muhide-orange)]"
                    style={{ width: `${Math.min(60, p.count * 6)}px` }}
                  />
                  <span className="font-medium text-[var(--text-secondary)] w-6 text-right">
                    {p.count}
                  </span>
                </div>
              </div>
            ))}
            {signals.trend.length === 0 && (
              <p className="text-xs text-[var(--text-disabled)]">
                {t("emp360.no_data")}
              </p>
            )}
          </div>
          <p className="mt-3 text-center text-[10px] text-[var(--text-disabled)]">
            {t("emp360.signals_total", { count: signals.total })}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
