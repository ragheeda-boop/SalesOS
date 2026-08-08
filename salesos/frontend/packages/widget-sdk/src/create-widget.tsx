"use client";

import { memo, useRef, useEffect, useCallback, type ReactNode } from "react";
import { Skeleton, useToast } from "@salesos/ui";
import { useWidgetLifecycle } from "./widget-lifecycle";
import { widgetTelemetry } from "./widget-telemetry";
import { checkPermissions } from "./widget-permissions";
import { isFeatureEnabled } from "./widget-feature-flags";
import type { WidgetConfig, WidgetStatus } from "./types";

const STATUS_LABEL: Record<WidgetStatus, string> = {
  ready: "",
  loading: "جاري التحميل...",
  degraded: "بيانات جزئية",
  error: "فشل التحميل",
};

const STATUS_COLOR: Record<WidgetStatus, string> = {
  ready: "#22C55E",
  loading: "#F59E0B",
  degraded: "#F97316",
  error: "#EF4444",
};

function WidgetCardFrame({
  title,
  status,
  minHeight,
  gridColumn,
  onRefresh,
  children,
}: {
  title: string;
  status: WidgetStatus;
  minHeight: string;
  gridColumn?: string;
  onRefresh?: () => void;
  children: ReactNode;
}) {
  const showStatus = status !== "ready";
  return (
    <div
      style={{
        gridColumn,
        minHeight,
        borderRadius: "0.75rem",
        border: "1px solid var(--border-default)",
        background: "var(--bg-primary)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        height: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h3 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>{title}</h3>
          {showStatus && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.75rem",
                color: STATUS_COLOR[status],
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: STATUS_COLOR[status],
                }}
              />
              {STATUS_LABEL[status]}
            </span>
          )}
        </div>
        {onRefresh && status !== "loading" && (
          <button
            onClick={onRefresh}
            aria-label="Refresh"
            style={{
              border: "none",
              background: "transparent",
              cursor: "pointer",
              padding: "0.25rem",
              color: "var(--text-muted)",
              fontSize: "0.875rem",
            }}
          >
            ↻
          </button>
        )}
      </div>
      <div style={{ flex: 1, padding: "1rem" }}>{children}</div>
    </div>
  );
}

function LoadingState({ minHeight }: { minHeight: string }) {
  return (
    <div
      aria-label="Loading"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: `calc(${minHeight} - 3.5rem)`,
        padding: "1rem",
      }}
    >
      <Skeleton variant="card" className="h-full w-full" />
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      role="alert"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: 120,
        color: "var(--danger-700, #991b1b)",
        fontSize: "0.875rem",
      }}
    >
      <span style={{ fontSize: "1.5rem" }}>⚠</span>
      <p style={{ margin: "0.5rem 0 0", fontWeight: 500 }}>تعذر تحميل البيانات</p>
      <p
        style={{ margin: "0.25rem 0 0", fontSize: "0.75rem", color: "var(--danger-600, #b91c1c)" }}
      >
        {message}
      </p>
      <button
        onClick={onRetry}
        style={{
          marginTop: "0.75rem",
          padding: "0.375rem 0.75rem",
          borderRadius: "0.375rem",
          border: "1px solid var(--danger-300, #fca5a5)",
          background: "transparent",
          color: "var(--danger-700, #991b1b)",
          cursor: "pointer",
          fontSize: "0.75rem",
        }}
      >
        إعادة المحاولة
      </button>
    </div>
  );
}

export function createWidget<T>(config: WidgetConfig<T>) {
  const WidgetComponent = memo(function WidgetComponent() {
    const timerRef = useRef<ReturnType<typeof widgetTelemetry.startTimer> | null>(null);
    const { data, status, lastUpdated, error, refetch } = config.useData();
    const telemetrySent = useRef(false);
    const prevStatusRef = useRef(status);
    const { toast } = useToast();

    const handleRefresh = useCallback(() => {
      config.lifecycle?.onRefresh?.({ id: config.metadata.id, metadata: config.metadata });
      widgetTelemetry.record("widget.refreshed", config.metadata.id);
      refetch();
    }, [refetch]);

    useWidgetLifecycle(config.metadata.id, config.metadata, status, config.lifecycle);

    useEffect(() => {
      timerRef.current = widgetTelemetry.startTimer(config.metadata.id);
      widgetTelemetry.record("widget.mounted", config.metadata.id);

      return () => {
        widgetTelemetry.record("widget.unmounted", config.metadata.id);
        timerRef.current?.stop("widget.render");
      };
    }, []);

    useEffect(() => {
      if (status === "error" && !telemetrySent.current) {
        widgetTelemetry.record("widget.failed", config.metadata.id, {
          error: error?.message ?? "unknown",
          status,
        });
        config.lifecycle?.onError?.({
          id: config.metadata.id,
          metadata: config.metadata,
          error: error ?? new Error("unknown"),
        });
        toast({
          variant: "error",
          title: `فشل تحميل: ${config.metadata.title}`,
          description: error?.message,
        });
        telemetrySent.current = true;
        return;
      }
      if (data && (status === "ready" || status === "degraded") && !telemetrySent.current) {
        widgetTelemetry.record("widget.loaded", config.metadata.id, { status });
        telemetrySent.current = true;
        return;
      }
    }, [data, status, error, toast]);

    useEffect(() => {
      if (prevStatusRef.current !== status) {
        prevStatusRef.current = status;
        telemetrySent.current = false;
      }
    }, [status]);

    // Permission check
    if (!checkPermissions(config.metadata.permissions)) {
      return config.fallback ?? null;
    }

    // Feature flag check
    if (!isFeatureEnabled(config.metadata.featureFlag)) {
      return config.fallback ?? null;
    }

    const minHeight = config.metadata.minHeight ?? "200px";

    return (
      <WidgetCardFrame
        title={config.metadata.title}
        status={status}
        minHeight={minHeight}
        gridColumn={config.metadata.gridColumn}
        onRefresh={handleRefresh}
      >
        {status === "loading" && <LoadingState minHeight={minHeight} />}
        {status === "error" && (
          <ErrorState message={error?.message ?? ""} onRetry={handleRefresh} />
        )}
        {status === "ready" &&
          config.render({
            data: data!,
            status,
            lastUpdated,
            metadata: config.metadata,
            refresh: handleRefresh,
          })}
        {status === "degraded" && data && (
          <div style={{ position: "relative" }}>
            <div style={{ opacity: 0.5 }}>
              {config.render({
                data,
                status,
                lastUpdated,
                metadata: config.metadata,
                refresh: handleRefresh,
              })}
            </div>
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.75rem",
                color: "var(--muhide-orange)",
                pointerEvents: "none",
              }}
            >
              بيانات جزئية — بعض المصادر غير متاحة
            </div>
          </div>
        )}
        {status === "degraded" && !data && <LoadingState minHeight={minHeight} />}
      </WidgetCardFrame>
    );
  });

  WidgetComponent.displayName = `Widget(${config.metadata.title})`;
  return WidgetComponent;
}
