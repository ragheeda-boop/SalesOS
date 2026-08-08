"use client";
/* eslint-disable custom-rules/no-hardcoded-colors */

import { type ReactNode } from "react";
import type { DashboardWidget, WidgetStatus } from "@/application/dashboard/widget.contract";
import { DashboardErrorBoundary } from "../_layout/dashboard-error-boundary";
import { getWidgetConfig, type WidgetId } from "../_registry/widget-config";
import { useTranslation } from "@/lib/i18n";

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

interface WidgetCardProps<T> {
  widget: DashboardWidget<T>;
  widgetId: WidgetId;
  children: ReactNode;
}

export function WidgetCard<T>({ widget, widgetId, children }: WidgetCardProps<T>) {
  const { t } = useTranslation();
  const config = getWidgetConfig(widgetId);
  const showStatus = widget.status !== "ready";
  const title = t(`dashboard.widget.${widgetId}`);

  return (
    <DashboardErrorBoundary widgetId={widgetId}>
      <div
        style={{
          gridColumn: config.gridColumn,
          minHeight: config.minHeight,
          borderRadius: "0.75rem",
          border: "1px solid var(--border-default)",
          background: "var(--bg-primary)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
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
                  color: STATUS_COLOR[widget.status],
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: STATUS_COLOR[widget.status],
                  }}
                />
                {STATUS_LABEL[widget.status]}
              </span>
            )}
          </div>
        </div>
        <div style={{ flex: 1, padding: "1rem" }}>
          {widget.status === "loading" && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                minHeight: 120,
              }}
            >
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  border: "3px solid var(--border-default)",
                  borderTopColor: "var(--muhide-orange)",
                  animation: "spin 0.8s linear infinite",
                }}
              />
            </div>
          )}
          {widget.status === "error" && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                minHeight: 120,
                color: "var(--danger-700, #991b1b)",
                fontSize: "0.875rem",
              }}
            >
              <span>⚠</span>
              <p style={{ margin: "0.5rem 0 0" }}>تعذر تحميل البيانات</p>
            </div>
          )}
          {widget.status === "ready" && widget.data !== null && children}
          {widget.status === "ready" && widget.data === null && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                minHeight: 120,
                color: "var(--text-muted)",
                fontSize: "0.875rem",
              }}
            >
              <p style={{ margin: 0 }}>لا توجد بيانات بعد</p>
            </div>
          )}
          {widget.status === "degraded" && (
            <>
              <div style={{ position: "relative" }}>
                <div style={{ opacity: 0.5, filter: "blur(0.5px)" }}>{children}</div>
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.75rem",
                    color: "#f97316",
                  }}
                >
                  بيانات جزئية — بعض المصادر غير متاحة
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </DashboardErrorBoundary>
  );
}
