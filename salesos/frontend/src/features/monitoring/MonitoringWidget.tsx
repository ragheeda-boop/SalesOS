"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

interface HealthItem {
  service: string;
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms: number;
}

const SERVICE_LABELS: Record<string, string> = {
  api: "API",
  database: "database",
  redis: "Redis",
  kafka: "Kafka",
  cache: "Cache",
  rate_limiter: "rate_limiter",
};

const STATUS_CONFIG: Record<string, { color: string; labelKey: string }> = {
  healthy: { color: "bg-success-500", labelKey: "monitoring.status.healthy" },
  degraded: { color: "bg-warning-500", labelKey: "monitoring.status.degraded" },
  unhealthy: {
    color: "bg-danger-500",
    labelKey: "monitoring.status.unhealthy",
  },
};

export function MonitoringWidget() {
  const { t } = useTranslation();
  const [health, setHealth] = useState<HealthItem[] | null>(null);
  const [lastKnown, setLastKnown] = useState<HealthItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await api.get("/api/v1/monitoring/health");
      const items: HealthItem[] = res.data;
      setHealth(items);
      setLastKnown(items);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30_000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-5 w-32 bg-[var(--bg-tertiary)] rounded" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-[var(--bg-tertiary)] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const displayData = health || lastKnown;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          {t("monitoring.service_health")}
        </h2>
        {error && (
          <span className="text-xs text-warning-600">
            {t("monitoring.stale_data")}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {(displayData || []).map((item) => {
          const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.unhealthy;
          return (
            <div
              key={item.service}
              className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">
                  {SERVICE_LABELS[item.service] || item.service}
                </span>
                <span
                  className={`inline-block w-2 h-2 rounded-full ${cfg.color}`}
                />
              </div>
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {t(cfg.labelKey)}
              </p>
              {item.latency_ms > 0 && (
                <p className="text-[10px] text-[var(--text-muted)]">
                  {item.latency_ms}ms
                </p>
              )}
            </div>
          );
        })}
        {(!displayData || displayData.length === 0) && (
          <div className="col-span-full rounded-xl border border-dashed border-[var(--border-default)] p-6 text-center">
            <p className="text-sm text-[var(--text-muted)]">
              {t("monitoring.no_data")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
