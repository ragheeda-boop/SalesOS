"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState } from "react";
import { Button, Spinner, useToast } from "@salesos/ui";
import { useCertifyConnector, useCertifyMeta } from "@/lib/hooks/integrationHubQueries";
import type { CertifyResult } from "@/lib/api";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/** Connector certification panel — CI adapters only; live HubSpot not claimed. */
export function SecondConnectorCertPanel() {
  const { toast } = useToast();
  const metaQuery = useCertifyMeta();
  const certifyMutation = useCertifyConnector();
  const [lastResult, setLastResult] = useState<CertifyResult | null>(null);
  const [key, setKey] = useState("hubspot");

  const certifiable = metaQuery.data?.certifiable ?? ["fake", "odoo", "hubspot"];

  function runCert(connectorKey: string) {
    certifyMutation.mutate(connectorKey, {
      onSuccess: (row) => {
        setLastResult(row);
        toast({
          title: row.ok ? "Certified" : "Certify returned",
          description: `${row.connector_key} · ok=${String(row.ok)}`,
          variant: row.ok ? "success" : "error",
        });
      },
      onError: (err) => {
        toast({
          title: "Certify failed",
          description: getApiError(err),
          variant: "error",
        });
      },
    });
  }

  return (
    <div
      className="space-y-3 rounded border border-[var(--border-default)] p-4"
      data-testid="second-connector-cert"
    >
      <h2 className="text-sm font-semibold text-[var(--text-primary)]">Connector certification</h2>
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="second-connector-honesty"
      >
        In-memory / CI adapters only. Live HubSpot network is not claimed.
      </p>

      {metaQuery.isLoading ? (
        <Spinner />
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : metaQuery.data ? (
        <div
          className="space-y-1 text-xs text-[var(--text-muted)]"
          data-testid="second-connector-meta"
        >
          <p>
            Suite: {metaQuery.data.suite} · second connector: {metaQuery.data.second_connector_key}{" "}
            ({metaQuery.data.second_connector_target})
          </p>
          <p>Certifiable: {metaQuery.data.certifiable.join(", ")}</p>
        </div>
      ) : null}

      <label className="block text-xs text-[var(--text-muted)]">
        Connector
        <select
          className="mt-1 w-full max-w-xs rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 text-sm"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          data-testid="second-connector-key"
        >
          {certifiable.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          data-testid="second-connector-run"
          disabled={certifyMutation.isPending}
          onClick={() => runCert(key)}
        >
          {certifyMutation.isPending ? "Certifying…" : `Certify ${key}`}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          data-testid="second-connector-run-hubspot"
          disabled={certifyMutation.isPending}
          onClick={() => {
            setKey("hubspot");
            runCert("hubspot");
          }}
        >
          Certify hubspot
        </Button>
      </div>

      {lastResult ? (
        <div
          className="space-y-1 rounded bg-[var(--bg-muted)] p-2 text-xs"
          data-testid="second-connector-result"
        >
          <p>
            <span className="text-[var(--text-muted)]">Connector: </span>
            {lastResult.connector_key}
          </p>
          <p>
            <span className="text-[var(--text-muted)]">Status: </span>
            {lastResult.ok ? "ok" : "failed"}
          </p>
          {"message" in lastResult && lastResult.message ? (
            <p>
              <span className="text-[var(--text-muted)]">Message: </span>
              {String(lastResult.message)}
            </p>
          ) : null}
          {"latency_ms" in lastResult && lastResult.latency_ms != null ? (
            <p>
              <span className="text-[var(--text-muted)]">Latency: </span>
              {String(lastResult.latency_ms)} ms
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
