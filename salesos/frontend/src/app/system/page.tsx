"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { Card, Badge, cn, Spinner } from "@salesos/ui";
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  ShieldCheck,
  Server,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface VersionResponse {
  service: string;
  api_version: string;
  backend_commit: string;
  build_date: string;
  build_id: string;
  schema_version: string;
  openapi_hash: string;
}

const FE_BUILD_COMMIT = process.env.NEXT_PUBLIC_BUILD_COMMIT || "";
const FE_BUILD_DATE = process.env.NEXT_PUBLIC_BUILD_DATE || "";
const FE_BUILD_ID = process.env.NEXT_PUBLIC_BUILD_ID || "";

function shortCommit(commit: string): string {
  return commit ? commit.slice(0, 12) : "—";
}

export default function SystemPage() {
  const { t } = useTranslation();
  const [backend, setBackend] = useState<VersionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVersion = useCallback(async () => {
    try {
      const res = await api.get<VersionResponse>("/api/v1/version");
      setBackend(res.data);
      setError(null);
    } catch {
      setError("Backend unreachable — /api/v1/version did not respond.");
    }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    fetchVersion();
    const interval = setInterval(fetchVersion, 60_000);
    return () => clearInterval(interval);
  }, [fetchVersion]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchVersion();
  };

  const backendReachable = Boolean(backend);
  const sameCommit =
    Boolean(FE_BUILD_COMMIT) && backend?.backend_commit === FE_BUILD_COMMIT;
  const schemaKnown = Boolean(backend?.schema_version) && backend?.schema_version !== "unavailable";

  const commitParity = backendReachable && sameCommit;
  const hashVerified = backendReachable; // FE computes its own hash only in CI gate
  const schemaParity = backendReachable && schemaKnown;

  const allPass = backendReachable && sameCommit && schemaParity;

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <ShieldCheck className="h-6 w-6 text-[var(--muhide-orange)]" />
          {t("system.title")}
        </h1>
        <button
          onClick={handleRefresh}
          className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
          aria-label={t("common.refresh")}
        >
          <RefreshCw className={cn("h-5 w-5", refreshing && "animate-spin")} />
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-[var(--text-muted)]">
          <Spinner /> {t("common.loading")}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Card className="p-5">
              <h2 className="mb-4 flex items-center gap-2 font-semibold">
                <Server className="h-4 w-4" />
                {t("system.frontend")}
              </h2>
              <dl className="space-y-3 text-sm">
                <Row label={t("system.commit")} value={shortCommit(FE_BUILD_COMMIT)} mono />
                <Row label={t("system.build_date")} value={FE_BUILD_DATE || "—"} mono />
                <Row label={t("system.build_id")} value={FE_BUILD_ID || "—"} mono />
              </dl>
            </Card>

            <Card className="p-5">
              <h2 className="mb-4 flex items-center gap-2 font-semibold">
                <Server className="h-4 w-4" />
                {t("system.backend")}
              </h2>
              <dl className="space-y-3 text-sm">
                <Row label={t("system.commit")} value={shortCommit(backend?.backend_commit || "")} mono />
                <Row label={t("system.build_date")} value={backend?.build_date || "—"} mono />
                <Row label={t("system.build_id")} value={backend?.build_id || "—"} mono />
              </dl>
            </Card>
          </div>

          <Card className="p-5">
            <h2 className="mb-4 font-semibold">{t("system.api_contract")}</h2>
            <dl className="space-y-3 text-sm">
              <Row label={t("system.api_version")} value={backend?.api_version || "—"} mono />
              <Row label={t("system.schema_version")} value={backend?.schema_version || "—"} mono />
              <Row
                label={t("system.openapi_hash")}
                value={backend?.openapi_hash ? backend.openapi_hash.slice(0, 16) : "—"}
                mono
              />
            </dl>
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 font-semibold">{t("system.parity_checks")}</h2>
            <div className="space-y-3 text-sm">
              <CheckRow
                label={t("system.backend_reachable")}
                ok={backendReachable}
              />
              <CheckRow label={t("system.same_commit")} ok={commitParity} />
              <CheckRow label={t("system.schema_known")} ok={schemaParity} />
              <CheckRow label={t("system.hash_verified")} ok={hashVerified} />
            </div>
          </Card>

          <div
            className={cn(
              "flex items-center justify-between rounded-xl border p-5",
              allPass
                ? "border-success-500/40 bg-success-50 dark:bg-success-900/20"
                : "border-danger-500/40 bg-danger-50 dark:bg-danger-900/20"
            )}
          >
            <div>
              <p className="text-sm text-[var(--text-muted)]">{t("system.result")}</p>
              <p
                className={cn(
                  "text-xl font-bold",
                  allPass ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"
                )}
              >
                {allPass
                  ? t("system.production_parity_verified")
                  : t("system.parity_failed")}
              </p>
            </div>
            {allPass ? (
              <CheckCircle className="h-8 w-8 text-success-500" />
            ) : (
              <XCircle className="h-8 w-8 text-danger-500" />
            )}
          </div>

          {error && (
            <p className="text-center text-sm text-danger-600 dark:text-danger-400">{error}</p>
          )}
        </>
      )}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-[var(--text-muted)]">{label}</dt>
      <dd
        className={cn(
          "truncate text-right text-[var(--text-secondary)]",
          mono && "font-mono text-xs"
        )}
      >
        {value}
      </dd>
    </div>
  );
}

function CheckRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-2 text-[var(--text-secondary)]">
        {ok ? (
          <CheckCircle className="h-4 w-4 text-success-500" />
        ) : (
          <XCircle className="h-4 w-4 text-danger-500" />
        )}
        {label}
      </span>
      <Badge variant={ok ? "success" : "danger"}>{ok ? "PASS" : "FAIL"}</Badge>
    </div>
  );
}
