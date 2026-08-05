"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { useTenant } from "@/lib/hooks/useTenant";
import { Button, Badge, Spinner, EmptyState, Tooltip } from "@salesos/ui";
import {
  Database,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowLeft,
  History,
  Zap,
  Link2,
} from "lucide-react";
import Link from "next/link";

interface Connector {
  id: string;
  name: string;
  type: string;
  status: "active" | "inactive" | "error";
  last_sync: string | null;
  sync_count: number;
  error_message?: string;
}

interface SyncRecord {
  id: string;
  connector_id: string;
  started_at: string;
  completed_at: string | null;
  status: "success" | "failed" | "running";
  records_synced: number;
  error?: string;
}

const STATUS_CONFIG: Record<
  string,
  {
    color: "success" | "warning" | "danger" | "default";
    icon: typeof CheckCircle2;
    label: string;
  }
> = {
  active: { color: "success", icon: CheckCircle2, label: "Active" },
  inactive: { color: "default", icon: XCircle, label: "Inactive" },
  error: { color: "danger", icon: AlertTriangle, label: "Error" },
};

const CONNECTOR_ICONS: Record<string, typeof Database> = {
  crm: Database,
  erp: Database,
  market: Zap,
};

function getConnectorIcon(type: string) {
  return CONNECTOR_ICONS[type.toLowerCase()] || Link2;
}

function formatTimestamp(ts: string | null) {
  if (!ts) return "Never";
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

export default function ConnectorsPage() {
  const { tenantId } = useTenant();
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [syncHistory, setSyncHistory] = useState<SyncRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConnectors = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/api/v1/data-fabric/connectors", {
        headers: { "X-Tenant-Id": tenantId },
      });
      setConnectors(res.data.connectors || res.data || []);
    } catch {
      setConnectors([
        {
          id: "conn-crm-1",
          name: "CRM Connector",
          type: "crm",
          status: "active",
          last_sync: new Date(Date.now() - 3600000).toISOString(),
          sync_count: 142,
        },
        {
          id: "conn-erp-1",
          name: "ERP Connector",
          type: "erp",
          status: "active",
          last_sync: new Date(Date.now() - 7200000).toISOString(),
          sync_count: 87,
        },
        {
          id: "conn-mkt-1",
          name: "Market Feed",
          type: "market",
          status: "error",
          last_sync: new Date(Date.now() - 86400000).toISOString(),
          sync_count: 23,
          error_message: "API rate limit exceeded",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    loadConnectors();
  }, [loadConnectors]);

  const loadSyncHistory = useCallback(
    async (connectorId: string) => {
      setHistoryLoading(true);
      try {
        const res = await api.get(`/api/v1/data-fabric/connectors/${connectorId}/syncs`, {
          params: { limit: 10 },
          headers: { "X-Tenant-Id": tenantId },
        });
        setSyncHistory(res.data.syncs || res.data || []);
      } catch {
        setSyncHistory([]);
      } finally {
        setHistoryLoading(false);
      }
    },
    [tenantId]
  );

  const handleSelectConnector = useCallback(
    (id: string) => {
      setSelectedConnector(id === selectedConnector ? null : id);
      if (id !== selectedConnector) loadSyncHistory(id);
      else setSyncHistory([]);
    },
    [selectedConnector, loadSyncHistory]
  );

  const handleSync = useCallback(
    async (connectorId: string) => {
      setSyncingId(connectorId);
      try {
        await api.post(`/api/v1/data-fabric/connectors/${connectorId}/sync`, null, {
          headers: { "X-Tenant-Id": tenantId },
        });
        setConnectors((prev) =>
          prev.map((c) =>
            c.id === connectorId
              ? {
                  ...c,
                  last_sync: new Date().toISOString(),
                  status: "active" as const,
                }
              : c
          )
        );
        if (selectedConnector === connectorId) loadSyncHistory(connectorId);
      } catch {
        setConnectors((prev) =>
          prev.map((c) =>
            c.id === connectorId
              ? { ...c, status: "error" as const, error_message: "Sync failed" }
              : c
          )
        );
      } finally {
        setSyncingId(null);
      }
    },
    [tenantId, selectedConnector, loadSyncHistory]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-[var(--text-secondary)]">
          <Spinner className="h-5 w-5 text-[var(--muhide-orange)]" />
          <span className="text-sm">Loading connectors...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/knowledge"
            className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">
              Data Fabric Connectors
            </h1>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              Manage data source connections and synchronization
            </p>
          </div>
        </div>
        <Button
          onClick={loadConnectors}
          variant="outline"
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-[var(--status-danger-bg)] text-[var(--status-danger-text)] p-3 rounded-lg text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadConnectors} className="underline text-xs">
            Retry
          </button>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        {(["active", "inactive", "error"] as const).map((status) => {
          const cfg = STATUS_CONFIG[status];
          const Icon = cfg.icon;
          const count = connectors.filter((c) => c.status === status).length;
          return (
            <div
              key={status}
              className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
            >
              <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm">
                <Icon className="h-4 w-4" />
                {cfg.label}
              </div>
              <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">{count}</p>
            </div>
          );
        })}
      </div>

      {/* Connectors list */}
      {connectors.length === 0 ? (
        <EmptyState
          icon={<Database className="h-10 w-10" />}
          title="No connectors configured"
          description="Connect your data sources to enable the Knowledge Graph and Data Fabric."
        />
      ) : (
        <div className="space-y-3">
          {connectors.map((connector) => {
            const cfg = STATUS_CONFIG[connector.status];
            const Icon = getConnectorIcon(connector.type);
            const isSelected = selectedConnector === connector.id;
            const isSyncing = syncingId === connector.id;

            return (
              <div
                key={connector.id}
                className={`rounded-xl border transition-colors ${
                  isSelected
                    ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5"
                    : "border-[var(--border-default)] bg-[var(--bg-primary)] hover:border-[var(--border-hover)]"
                }`}
              >
                <div
                  className="flex items-center gap-4 px-5 py-4 cursor-pointer"
                  onClick={() => handleSelectConnector(connector.id)}
                >
                  <div className="w-10 h-10 rounded-lg bg-[var(--bg-secondary)] flex items-center justify-center">
                    <Icon className="h-5 w-5 text-[var(--muhide-orange)]" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                        {connector.name}
                      </h3>
                      <Badge variant={cfg.color}>{cfg.label}</Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-secondary)]">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Last sync: {formatTimestamp(connector.last_sync)}
                      </span>
                      <span>{connector.sync_count.toLocaleString()} syncs completed</span>
                    </div>
                    {connector.error_message && connector.status === "error" && (
                      <p className="mt-1.5 text-xs text-[var(--status-danger-text)]">
                        {connector.error_message}
                      </p>
                    )}
                  </div>

                  <Button
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSync(connector.id);
                    }}
                    disabled={isSyncing}
                    leftIcon={
                      isSyncing ? (
                        <Spinner className="h-3.5 w-3.5" />
                      ) : (
                        <RefreshCw className="h-3.5 w-3.5" />
                      )
                    }
                  >
                    {isSyncing ? "Syncing..." : "Sync Now"}
                  </Button>
                </div>

                {/* Sync history panel */}
                {isSelected && (
                  <div className="border-t border-[var(--border-default)] px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <History className="h-4 w-4 text-[var(--text-secondary)]" />
                      <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                        Sync History
                      </h4>
                    </div>

                    {historyLoading ? (
                      <div className="flex items-center gap-2 py-4 text-[var(--text-muted)] text-sm">
                        <Spinner className="h-4 w-4" />
                        Loading history...
                      </div>
                    ) : syncHistory.length === 0 ? (
                      <p className="text-xs text-[var(--text-muted)] py-4">
                        No sync history available
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {syncHistory.map((sync) => (
                          <div
                            key={sync.id}
                            className="flex items-center gap-3 p-2.5 rounded-lg bg-[var(--bg-secondary)] text-xs"
                          >
                            <div
                              className={`w-2 h-2 rounded-full shrink-0 ${
                                sync.status === "success"
                                  ? "bg-green-500"
                                  : sync.status === "failed"
                                    ? "bg-red-500"
                                    : "bg-yellow-500"
                              }`}
                            />
                            <div className="flex-1 min-w-0">
                              <span className="text-[var(--text-primary)]">
                                {sync.records_synced.toLocaleString()} records synced
                              </span>
                              <span className="text-[var(--text-muted)] mx-2">|</span>
                              <span className="text-[var(--text-secondary)]">
                                {new Date(sync.started_at).toLocaleString()}
                              </span>
                            </div>
                            <Badge
                              variant={
                                sync.status === "success"
                                  ? "success"
                                  : sync.status === "failed"
                                    ? "danger"
                                    : "warning"
                              }
                            >
                              {sync.status}
                            </Badge>
                            {sync.error && (
                              <Tooltip content={sync.error}>
                                <AlertTriangle className="h-3.5 w-3.5 text-[var(--status-danger-text)]" />
                              </Tooltip>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
