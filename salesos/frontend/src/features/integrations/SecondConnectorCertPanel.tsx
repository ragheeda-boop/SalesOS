"use client";

import { useState } from "react";
import { Button, Spinner, useToast } from "@salesos/ui";
import {
  useCertifyConnector,
  useCertifyMeta,
} from "@/lib/hooks/integrationHubQueries";
import type { CertifyResult } from "@/lib/api";
import {
  SECOND_CONNECTOR_HONESTY,
  SECOND_CONNECTOR_NON_GOALS,
} from "@/features/integrations/secondConnectorHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/** FE-S11-10 — tip STORY-11-10 certify surface. Not Production GO. */
export function SecondConnectorCertPanel() {
  const { toast } = useToast();
  const metaQuery = useCertifyMeta();
  const certifyMutation = useCertifyConnector();
  const [lastResult, setLastResult] = useState<CertifyResult | null>(null);
  const [key, setKey] = useState("hubspot");

  const certifiable = metaQuery.data?.certifiable ?? [
    "fake",
    "odoo",
    "hubspot",
  ];

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
      <h2 className="text-sm font-semibold text-[var(--text-primary)]">
        Second connector certification (STORY-11-10)
      </h2>
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="second-connector-honesty"
      >
        {SECOND_CONNECTOR_HONESTY} Non-goals:{" "}
        {SECOND_CONNECTOR_NON_GOALS.join("; ")}.
      </p>

      {metaQuery.isLoading ? (
        <Spinner />
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">
          {getApiError(metaQuery.error)}
        </p>
      ) : metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="second-connector-meta"
        >
          <p>
            suite={metaQuery.data.suite} · second=
            {metaQuery.data.second_connector_key} (
            {metaQuery.data.second_connector_target})
          </p>
          <p>certifiable: {metaQuery.data.certifiable.join(", ")}</p>
          <p data-testid="second-connector-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
        </div>
      ) : null}

      <label className="block text-xs text-[var(--text-muted)]">
        connector_key
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
        <pre
          className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
          data-testid="second-connector-result"
        >
          {JSON.stringify(lastResult, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
