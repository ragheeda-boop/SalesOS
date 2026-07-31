"use client";

import { Cable, CheckCircle, XCircle, Clock, Database } from "lucide-react";
import type { MCPData } from "./types";

export function MCPView({ data }: { data: MCPData }) {
  return (
    <div
      role="region"
      aria-label="اتصالات MCP"
      className="space-y-2/20 dark:rounded-lg dark:p-1"
    >
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <p className="text-[9px] text-[var(--text-muted)]">الاتصالات</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">
            {data.totalConnections}
          </p>
        </div>
        <div className="rounded-lg bg-[var(--status-success-bg)] p-2">
          <p className="text-[9px] text-[var(--status-success-text)]">نشطة</p>
          <p className="text-sm font-bold text-[var(--status-success-text)]">
            {data.activeConnections}
          </p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <p className="text-[9px] text-[var(--text-muted)]">الكيانات</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">
            {data.syncedEntities.toLocaleString()}
          </p>
        </div>
      </div>
      {data.connections.map((c) => (
        <div
          key={c.id}
          className="flex items-center gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]"
        >
          <Cable className="h-4 w-4 shrink-0 text-[var(--text-muted)]" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-[var(--text-primary)]">
                {c.name}
              </span>
              {c.status === "connected" ? (
                <CheckCircle className="h-3 w-3 text-[var(--status-success-text)]" />
              ) : c.status === "error" ? (
                <XCircle className="h-3 w-3 text-[var(--status-danger-text)]" />
              ) : (
                <Clock className="h-3 w-3 text-[var(--status-warning-text)]" />
              )}
            </div>
            <div className="flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
              <span>{c.type}</span>
              <span>·</span>
              <Database className="h-2.5 w-2.5" /> {c.entities} كيان
              {c.lastSync && (
                <span>
                  · آخر مزامنة:{" "}
                  {new Date(c.lastSync).toLocaleDateString("ar-SA")}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
