"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useActiveHubMapping,
  useCreateHubConnection,
  useCreateHubMapping,
  useDisconnectHubConnection,
  useHubConflictPolicy,
  useHubConnection,
  useHubConnections,
  useHubSyncRuns,
  useHubUnlinkedBadges,
  usePutHubConflictPolicy,
  useScheduleHubSync,
  useTestHubConnection,
} from "@/lib/hooks/integrationHubQueries";
import { STUDIO_STEPS } from "@/features/admin/IntegrationsStudioShell";
import type { HubConnection, HubScheduleResult } from "@/lib/api";
import {
  buildStudioSearchParams,
  parseRunModelFilter,
  parseRunStatusFilter,
  parseStudioStep,
  type StudioStepId,
} from "@/features/integrations/studioUrl";
import {
  CANONICAL_OPPORTUNITY_STAGES,
  DEFAULT_OPPORTUNITY_MAPPINGS,
  HUB_MODEL_PRESETS,
  isOpportunityModel,
} from "@/features/integrations/odooOpportunityHonesty";
import {
  DEFAULT_PARTNER_MAPPINGS,
  isPartnerModel,
} from "@/features/integrations/odooPartnerHonesty";
import { DEFAULT_NOTE_MAPPINGS, isNoteModel } from "@/features/integrations/odooNoteHonesty";
import {
  CANONICAL_TICKET_STAGES,
  DEFAULT_TICKET_MAPPINGS,
  isTicketModel,
} from "@/features/integrations/odooTicketHonesty";
import { DEFAULT_TASK_MAPPINGS, isTaskModel } from "@/features/integrations/odooTaskHonesty";
import {
  CUSTOMER_MOVE_TYPES,
  DEFAULT_INVOICE_MAPPINGS,
  isInvoiceModel,
} from "@/features/integrations/odooInvoiceHonesty";
import {
  FLAG_ODOO_INTEGRATION,
  ODOO_FLAG_GATED_ACTIONS,
  isOdooConnectorKey,
} from "@/features/integrations/odooIncrementalHonesty";
import {
  TIP_OPERATIONAL_FIELDS,
  TIP_SALESOS_AUTHORED_FIELDS,
  tipDefaultConflictRules,
} from "@/features/integrations/hubConflictDefaults";

export type { StudioStepId };

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

function csvFromList(values: string[] | undefined): string {
  return (values || []).join(", ");
}

function listFromCsv(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Tip STORY-09-09 SyncRunResponse cursor watermarks for Monitor rows. */
function syncRunHasCursors(run: {
  cursor_before?: Record<string, unknown> | null;
  cursor_after?: Record<string, unknown> | null;
}): boolean {
  return (
    Object.keys(run.cursor_before ?? {}).length > 0 ||
    Object.keys(run.cursor_after ?? {}).length > 0
  );
}

/**
 * STORY-08-07 / FE-S08-08 — Integrations Studio against Hub HTTP.
 * Connect / test / map / conflict-policy / schedule / monitor / disconnect.
 * Tip STORY-09-01: connector_key `odoo` dispatches OdooAdapter.test_connection.
 * Active mapping GET (FE-S08-09). URL deep-link (FE-S08-11). STORY-09-02: schedule/map `crm.lead` uses translated stages (no raw Odoo stage passthrough).
 * STORY-09-02 opportunity stage honesty (FE-S09-02).
 * STORY-09-01 partner/cr_number honesty (FE-S09-01).
 * STORY-09-03 InteractionNote PII honesty (FE-S09-03).
 * STORY-09-04 SupportTicket stage honesty (FE-S09-04).
 * STORY-09-05 TaskCaseExtension VO honesty (FE-S09-05).
 * STORY-09-06 CustomerInvoice payment honesty (FE-S09-06).
 * STORY-09-07 feature_odoo_integration + write_date cursor (FE-S09-07).
 * Unlinked badge list API not live. Not Production GO.
 */
export function IntegrationsStudio() {
  const { toast } = useToast();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [step, setStep] = useState<StudioStepId>("connect");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [urlHydrated, setUrlHydrated] = useState(false);
  const [name, setName] = useState("Fake connector");
  const [connectorKey, setConnectorKey] = useState("fake");
  const [credentialRef, setCredentialRef] = useState("vault:demo/fake");
  const [configJson, setConfigJson] = useState("{}");
  const [model, setModel] = useState("res.partner");
  const [mappingJson, setMappingJson] = useState(() =>
    JSON.stringify(DEFAULT_PARTNER_MAPPINGS, null, 2)
  );
  const [baselineCsv, setBaselineCsv] = useState("name, email, phone, cr_number");
  const [mappingVersion, setMappingVersion] = useState(1);
  const [scheduleName, setScheduleName] = useState("");
  const [disconnectConfirmed, setDisconnectConfirmed] = useState(false);
  const [schedule, setSchedule] = useState("15m");
  const [scheduleJobType, setScheduleJobType] = useState<"interval" | "cron" | "one_time">(
    "interval"
  );
  const [connectionActiveFilter, setConnectionActiveFilter] = useState<
    "all" | "active" | "inactive"
  >("all");
  const [lastTest, setLastTest] = useState<string>("");
  const [lastSchedule, setLastSchedule] = useState<HubScheduleResult | null>(null);
  const [monitorStatusFilter, setMonitorStatusFilter] = useState("all");
  const [monitorModelFilter, setMonitorModelFilter] = useState("all");
  const [rulesJson, setRulesJson] = useState("[]");
  const [authoredCsv, setAuthoredCsv] = useState("");
  const [operationalCsv, setOperationalCsv] = useState("");

  const connectionsQuery = useHubConnections();
  const connectionDetailQuery = useHubConnection(selectedId);
  const syncRunsQuery = useHubSyncRuns(selectedId);
  const unlinkedBadgesQuery = useHubUnlinkedBadges(selectedId);
  const conflictQuery = useHubConflictPolicy(step === "conflict" ? selectedId : null);
  const activeMappingQuery = useActiveHubMapping(step === "map" ? selectedId : null, model);
  const createMutation = useCreateHubConnection();
  const testMutation = useTestHubConnection();
  const mapMutation = useCreateHubMapping();
  const conflictMutation = usePutHubConflictPolicy();
  const scheduleMutation = useScheduleHubSync();
  const disconnectMutation = useDisconnectHubConnection();

  const connections = connectionsQuery.data || [];
  const filteredConnections = useMemo(() => {
    if (connectionActiveFilter === "all") return connections;
    const wantActive = connectionActiveFilter === "active";
    return connections.filter((c) => Boolean(c.is_active) === wantActive);
  }, [connections, connectionActiveFilter]);
  const selected: HubConnection | undefined = useMemo(() => {
    if (connectionDetailQuery.data && connectionDetailQuery.data.id === selectedId) {
      return connectionDetailQuery.data;
    }
    return connections.find((c) => c.id === selectedId);
  }, [connections, selectedId, connectionDetailQuery.data]);
  const filteredSyncRuns = useMemo(() => {
    const rows = syncRunsQuery.data || [];
    return rows.filter((r) => {
      if (monitorStatusFilter !== "all") {
        if ((r.status || "").toLowerCase() !== monitorStatusFilter.toLowerCase()) {
          return false;
        }
      }
      if (monitorModelFilter !== "all") {
        if ((r.model || "").trim() !== monitorModelFilter.trim()) {
          return false;
        }
      }
      return true;
    });
  }, [syncRunsQuery.data, monitorStatusFilter, monitorModelFilter]);

  const monitorModelOptions = useMemo(() => {
    const set = new Set<string>();
    for (const row of syncRunsQuery.data || []) {
      const m = (row.model || "").trim();
      if (m) set.add(m);
    }
    return Array.from(set).sort();
  }, [syncRunsQuery.data]);

  useEffect(() => {
    const policy = conflictQuery.data;
    if (!policy) return;
    setRulesJson(JSON.stringify(policy.rules ?? [], null, 2));
    setAuthoredCsv(csvFromList(policy.salesos_authored_fields));
    setOperationalCsv(csvFromList(policy.operational_fields));
  }, [conflictQuery.data]);

  useEffect(() => {
    const mapping = activeMappingQuery.data;
    if (!mapping) return;
    // Do not overwrite user/model presets (e.g. crm.lead) with a mismatched
    // active mapping payload from another model.
    if (mapping.model && mapping.model !== model.trim()) return;
    setMappingJson(JSON.stringify(mapping.mappings ?? [], null, 2));
    setBaselineCsv(csvFromList(mapping.baseline_fields));
    if (typeof mapping.version === "number") {
      setMappingVersion(mapping.version);
    }
  }, [activeMappingQuery.data, model]);

  useEffect(() => {
    setDisconnectConfirmed(false);
  }, [selectedId]);

  useEffect(() => {
    if (urlHydrated) return;
    const parsed = parseStudioStep(searchParams.get("step"));
    if (parsed) setStep(parsed);
    const connection = searchParams.get("connection");
    if (connection) setSelectedId(connection);
    setMonitorStatusFilter(parseRunStatusFilter(searchParams.get("runStatus")));
    setMonitorModelFilter(parseRunModelFilter(searchParams.get("runModel")));
    setUrlHydrated(true);
  }, [searchParams, urlHydrated]);

  useEffect(() => {
    if (!urlHydrated) return;
    const next = buildStudioSearchParams({
      step,
      connectionId: selectedId,
      runStatus: monitorStatusFilter,
      runModel: monitorModelFilter,
    });
    const current = searchParams.toString() ? `?${searchParams.toString()}` : "";
    if (next === current) return;
    router.replace(`${pathname}${next}`, { scroll: false });
  }, [
    step,
    selectedId,
    monitorStatusFilter,
    monitorModelFilter,
    urlHydrated,
    pathname,
    router,
    searchParams,
  ]);

  function applyModelPreset(nextModel: string) {
    setModel(nextModel);
    if (isOpportunityModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_OPPORTUNITY_MAPPINGS, null, 2));
      setBaselineCsv("name, stage, amount, partner_external_id");
      return;
    }
    if (isNoteModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_NOTE_MAPPINGS, null, 2));
      setBaselineCsv("subject, body");
      return;
    }
    if (isTicketModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_TICKET_MAPPINGS, null, 2));
      setBaselineCsv("name, stage, priority, partner_external_id");
      return;
    }
    if (isTaskModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_TASK_MAPPINGS, null, 2));
      setBaselineCsv("name, stage");
      return;
    }
    if (isInvoiceModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_INVOICE_MAPPINGS, null, 2));
      setBaselineCsv("name, amount_total, amount_residual, payment_state, partner_external_id");
      return;
    }
    if (isPartnerModel(nextModel)) {
      setMappingJson(JSON.stringify(DEFAULT_PARTNER_MAPPINGS, null, 2));
      setBaselineCsv("name, email, phone, cr_number");
    }
  }

  const needsConnection = step !== "connect";

  return (
    <div className="space-y-4" data-testid="integrations-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="integrations-studio-live-honesty"
      >
        Do not paste real secrets into credential references. Odoo sync may be gated by a feature
        flag. Live HubSpot network is not claimed.
      </p>

      <ol
        className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
        data-testid="integrations-studio-steps"
      >
        {STUDIO_STEPS.map((item, index) => {
          const active = step === item.id;
          return (
            <li key={item.id}>
              <button
                type="button"
                data-testid={`integrations-studio-step-${item.id}`}
                onClick={() => setStep(item.id)}
                className={
                  active
                    ? "flex w-full min-h-[44px] items-center gap-2 rounded border border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/10 px-3 py-2 text-left text-sm"
                    : "flex w-full min-h-[44px] items-center gap-2 rounded border border-[var(--border-default)] px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                }
              >
                <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[var(--border-default)] text-xs">
                  {index + 1}
                </span>
                <span className="font-medium">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ol>

      <section
        className="rounded border border-[var(--border-default)] p-4 space-y-3"
        data-testid={`integrations-studio-panel-${step}`}
      >
        {needsConnection ? (
          <div className="space-y-2">
            <label className="block text-xs text-[var(--text-muted)]">Connection</label>
            {connectionsQuery.isLoading ? (
              <Spinner className="h-5 w-5" />
            ) : (
              <div className="space-y-2">
                <select
                  data-testid="integrations-studio-connection-active-filter"
                  className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={connectionActiveFilter}
                  onChange={(e) =>
                    setConnectionActiveFilter(e.target.value as "all" | "active" | "inactive")
                  }
                >
                  <option value="all">All connections</option>
                  <option value="active">Active only</option>
                  <option value="inactive">Inactive only</option>
                </select>
                <select
                  data-testid="integrations-studio-connection-select"
                  className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={selectedId || ""}
                  onChange={(e) => setSelectedId(e.target.value || null)}
                >
                  <option value="">Select a connection…</option>
                  {filteredConnections.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.connector_key}){c.is_active ? "" : " · inactive"}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {selected ? (
              <dl
                className="grid gap-1 rounded border border-[var(--border-default)] px-3 py-2 text-xs text-[var(--text-secondary)] sm:grid-cols-2"
                data-testid="integrations-studio-connection-detail"
              >
                <div>
                  <dt className="text-[var(--text-muted)]">Id</dt>
                  <dd className="flex flex-wrap items-center gap-2 font-mono break-all">
                    <span>{selected.id}</span>
                    <Button
                      data-testid="integrations-studio-copy-connection-id"
                      onClick={async () => {
                        try {
                          await navigator.clipboard.writeText(selected.id);
                          toast({
                            variant: "success",
                            title: "Connection id copied",
                            description: selected.id,
                          });
                        } catch {
                          toast({
                            variant: "error",
                            title: "Copy failed",
                            description: selected.id,
                          });
                        }
                      }}
                    >
                      Copy id
                    </Button>
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Connector</dt>
                  <dd data-testid="integrations-studio-connection-key">
                    {selected.connector_key}
                    {selected.is_active ? " · active" : " · inactive"}
                  </dd>
                  <Button
                    data-testid="integrations-studio-connection-refresh"
                    disabled={connectionDetailQuery.isFetching}
                    onClick={() => {
                      void connectionDetailQuery.refetch();
                      void connectionsQuery.refetch();
                    }}
                  >
                    {connectionDetailQuery.isFetching ? "Refreshing…" : "Refresh connection"}
                  </Button>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Credential ref</dt>
                  <dd className="font-mono break-all">{selected.credential_ref}</dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Cursor state</dt>
                  <dd className="break-all" data-testid="integrations-studio-connection-cursor">
                    {(() => {
                      const state = selected.cursor_state || {};
                      const keys = Object.keys(state);
                      if (keys.length === 0) return "No watermarks";
                      return `${keys.length} watermark(s): ${keys.slice(0, 6).join(", ")}${keys.length > 6 ? "…" : ""}`;
                    })()}
                  </dd>
                </div>
                {selected.created_at || selected.updated_at ? (
                  <div className="sm:col-span-2">
                    <dt className="text-[var(--text-muted)]">Timestamps</dt>
                    <dd
                      className="font-mono break-all"
                      data-testid="integrations-studio-connection-timestamps"
                    >
                      {selected.created_at ? `created ${selected.created_at}` : ""}
                      {selected.created_at && selected.updated_at ? " · " : ""}
                      {selected.updated_at ? `updated ${selected.updated_at}` : ""}
                    </dd>
                  </div>
                ) : null}
                {selected && isOdooConnectorKey(selected.connector_key) ? (
                  <div className="sm:col-span-2 space-y-2">
                    <p
                      className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                      data-testid="integrations-studio-odoo-flag-honesty"
                    >
                      Odoo actions may require the <code>{FLAG_ODOO_INTEGRATION}</code> flag (
                      {ODOO_FLAG_GATED_ACTIONS.join(", ")}).
                    </p>
                    <p
                      className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                      data-testid="integrations-studio-cursor-write-date-honesty"
                    >
                      Sync cursors use write_date watermarks when available.
                    </p>
                  </div>
                ) : null}
                <div className="sm:col-span-2">
                  <dt className="text-[var(--text-muted)]">Connection config keys</dt>
                  <dd className="break-all" data-testid="integrations-studio-connection-config">
                    {(() => {
                      const cfg = selected.connection_config || {};
                      const keys = Object.keys(cfg);
                      return keys.length ? keys.join(", ") : "No non-secret config keys";
                    })()}
                  </dd>
                </div>
              </dl>
            ) : null}
          </div>
        ) : null}

        {step === "connect" ? (
          <div className="space-y-3" data-testid="integrations-studio-connect">
            <Input
              label="Name"
              data-testid="integrations-studio-connect-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              label="Connector key"
              data-testid="integrations-studio-connect-key"
              value={connectorKey}
              onChange={(e) => setConnectorKey(e.target.value)}
            />
            <p className="text-xs text-[var(--text-muted)]">
              Connector keys: <code>fake</code>, <code>odoo</code>, or <code>hubspot</code> (CI
              adapter). Live HubSpot / XML-RPC needs a vault credential reference only — no
              passwords in this form.
            </p>
            <Input
              label="Credential ref"
              data-testid="integrations-studio-connect-cred"
              value={credentialRef}
              onChange={(e) => setCredentialRef(e.target.value)}
            />
            <p className="text-xs text-[var(--text-muted)]">
              Reference only — do not invent production secrets.
            </p>
            <label className="block text-xs text-[var(--text-muted)]">
              Connection config JSON (non-secret)
            </label>
            <textarea
              data-testid="integrations-studio-connect-config"
              className="min-h-[72px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 font-mono text-xs"
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
            />
            <p className="text-xs text-[var(--text-muted)]">
              Tip accepts non-secret `connection_config` only — never paste passwords here.
            </p>
            <Button
              data-testid="integrations-studio-connect-submit"
              disabled={createMutation.isPending}
              onClick={async () => {
                try {
                  const parsedConfig = JSON.parse(configJson || "{}") as Record<string, unknown>;
                  if (
                    parsedConfig === null ||
                    typeof parsedConfig !== "object" ||
                    Array.isArray(parsedConfig)
                  ) {
                    throw new Error("connection_config must be a JSON object");
                  }
                  const row = await createMutation.mutateAsync({
                    name: name.trim(),
                    connector_key: connectorKey.trim(),
                    credential_ref: credentialRef.trim(),
                    connection_config: parsedConfig,
                  });
                  setSelectedId(row.id);
                  setStep("test");
                  toast({
                    variant: "success",
                    title: "Connection created",
                    description: row.id,
                  });
                } catch (err) {
                  toast({
                    variant: "error",
                    title: "Connect failed",
                    description: getApiError(err),
                  });
                }
              }}
            >
              {createMutation.isPending ? "Creating…" : "Connect"}
            </Button>
          </div>
        ) : null}

        {step === "test" ? (
          <div className="space-y-3" data-testid="integrations-studio-test">
            <p className="text-sm text-[var(--text-secondary)]">
              Dispatches by selected <code>{selected?.connector_key || "connector_key"}</code>:{" "}
              <code>odoo</code> → OdooAdapter, else FakeSourceConnector.
            </p>
            <Button
              data-testid="integrations-studio-test-submit"
              disabled={!selectedId || testMutation.isPending}
              onClick={async () => {
                if (!selectedId) return;
                try {
                  const result = await testMutation.mutateAsync(selectedId);
                  const msg = result.ok
                    ? `OK · ${result.message} (${result.latency_ms}ms)`
                    : `Failed · ${result.message}`;
                  setLastTest(msg);
                  toast({
                    variant: result.ok ? "success" : "warning",
                    title: "Connection test",
                    description: msg,
                  });
                } catch (err) {
                  toast({
                    variant: "error",
                    title: "Test failed",
                    description: getApiError(err),
                  });
                }
              }}
            >
              {testMutation.isPending ? "Testing…" : "Test connection"}
            </Button>
            {lastTest ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-test-result"
              >
                {lastTest}
              </p>
            ) : null}
          </div>
        ) : null}

        {step === "map" ? (
          <div className="space-y-3" data-testid="integrations-studio-map">
            <div className="flex flex-wrap gap-2" data-testid="integrations-studio-model-presets">
              {HUB_MODEL_PRESETS.map((preset) => (
                <Button
                  key={preset.id}
                  data-testid={`integrations-studio-model-preset-${preset.id}`}
                  onClick={() => applyModelPreset(preset.model)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            {isPartnerModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-partner-join-honesty"
              >
                Partner sync maps commercial registration numbers to company records. Unlinked
                residuals appear on Monitor.
              </p>
            ) : null}
            {isOpportunityModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-opportunity-stage-honesty"
              >
                Opportunity stages are translated to canonical stages (
                {CANONICAL_OPPORTUNITY_STAGES.join(", ")}). Unmapped stages fail loudly.
              </p>
            ) : null}
            {isNoteModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-note-pii-honesty"
              >
                Note bodies are PII-scrubbed before any RAG-adjacent use. Raw body stays audit-only.
              </p>
            ) : null}
            {isTicketModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-ticket-stage-honesty"
              >
                Ticket stages map to {CANONICAL_TICKET_STAGES.join(", ")}. Unmapped stages fail
                loudly; descriptions are PII-scrubbed.
              </p>
            ) : null}
            {isTaskModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-task-case-honesty"
              >
                Tasks may include optional case extensions (financing / insurance). Stages are
                soft-mapped.
              </p>
            ) : null}
            {isInvoiceModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-invoice-payment-honesty"
              >
                Customer invoices (AR) are separate from platform Stripe billing. Move types:{" "}
                {CUSTOMER_MOVE_TYPES.join(", ")}.
              </p>
            ) : null}
            <Input
              label="Model"
              data-testid="integrations-studio-map-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button
                data-testid="integrations-studio-map-load"
                disabled={!selectedId || activeMappingQuery.isFetching}
                onClick={() => {
                  void activeMappingQuery.refetch();
                }}
              >
                {activeMappingQuery.isFetching ? "Loading…" : "Load active mapping"}
              </Button>
              <span
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-map-active-status"
              >
                {activeMappingQuery.isLoading
                  ? "Loading active mapping…"
                  : activeMappingQuery.data
                    ? `Active v${activeMappingQuery.data.version} · ${
                        activeMappingQuery.data.model
                      }${activeMappingQuery.data.is_active ? " · is_active" : " · inactive"}${
                        activeMappingQuery.data.id
                          ? ` · ${activeMappingQuery.data.id.slice(0, 8)}`
                          : ""
                      }`
                    : selectedId
                      ? "No active mapping for this model"
                      : "Select a connection"}
              </span>
            </div>
            <Input
              label="Baseline fields (csv)"
              data-testid="integrations-studio-map-baseline"
              value={baselineCsv}
              onChange={(e) => setBaselineCsv(e.target.value)}
            />
            <Input
              label="Mapping version (tip MappingCreate.version)"
              data-testid="integrations-studio-map-version"
              type="number"
              value={String(mappingVersion)}
              onChange={(e) => {
                const n = Number.parseInt(e.target.value, 10);
                setMappingVersion(Number.isFinite(n) && n > 0 ? n : 1);
              }}
            />
            <p className="text-xs text-[var(--text-muted)]">
              Tip `baseline_fields` on FieldMappingConfig — used for drift detection. Not Production
              GO.
            </p>
            <label className="block text-xs text-[var(--text-muted)]">Mappings JSON</label>
            <textarea
              data-testid="integrations-studio-map-json"
              className="min-h-[100px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 font-mono text-xs"
              value={mappingJson}
              onChange={(e) => setMappingJson(e.target.value)}
            />
            <Button
              data-testid="integrations-studio-map-submit"
              disabled={!selectedId || mapMutation.isPending}
              onClick={async () => {
                if (!selectedId) return;
                try {
                  const mappings = JSON.parse(mappingJson) as Record<string, unknown>[];
                  if (!Array.isArray(mappings)) {
                    throw new Error("mappings must be a JSON array");
                  }
                  await mapMutation.mutateAsync({
                    connectionId: selectedId,
                    body: {
                      model: model.trim(),
                      mappings,
                      baseline_fields: listFromCsv(baselineCsv),
                      version: mappingVersion,
                    },
                  });
                  toast({
                    variant: "success",
                    title: "Mapping saved",
                    description: model.trim(),
                  });
                } catch (err) {
                  toast({
                    variant: "error",
                    title: "Map failed",
                    description: getApiError(err),
                  });
                }
              }}
            >
              {mapMutation.isPending ? "Saving…" : "Save mapping"}
            </Button>
          </div>
        ) : null}

        {step === "conflict" ? (
          <div className="space-y-3" data-testid="integrations-studio-conflict">
            <p className="text-sm text-[var(--text-secondary)]">
              ConflictResolutionPolicy (OBJ-333) via GET/PUT <code>/conflict-policy</code>.
              SalesOS-authored fields stay exclude_from_pull (feedback-loop exclusion).
            </p>
            {!selectedId ? (
              <p className="text-sm text-[var(--text-muted)]">
                Select a connection to load policy.
              </p>
            ) : conflictQuery.isLoading ? (
              <Spinner className="h-5 w-5" />
            ) : (
              <>
                <label className="block text-xs text-[var(--text-muted)]">Rules JSON</label>
                <textarea
                  data-testid="integrations-studio-conflict-rules"
                  className="min-h-[120px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 font-mono text-xs"
                  value={rulesJson}
                  onChange={(e) => setRulesJson(e.target.value)}
                />
                <Input
                  label="SalesOS-authored fields (csv)"
                  data-testid="integrations-studio-conflict-authored"
                  value={authoredCsv}
                  onChange={(e) => setAuthoredCsv(e.target.value)}
                />
                <Input
                  label="Operational fields (csv)"
                  data-testid="integrations-studio-conflict-operational"
                  value={operationalCsv}
                  onChange={(e) => setOperationalCsv(e.target.value)}
                />
                <Button
                  data-testid="integrations-studio-conflict-tip-defaults"
                  onClick={() => {
                    setRulesJson(JSON.stringify(tipDefaultConflictRules(), null, 2));
                    setAuthoredCsv(TIP_SALESOS_AUTHORED_FIELDS.join(", "));
                    setOperationalCsv(TIP_OPERATIONAL_FIELDS.join(", "));
                    toast({
                      variant: "success",
                      title: "Tip conflict defaults loaded",
                      description: "Default conflict policy applied",
                    });
                  }}
                >
                  Load tip defaults
                </Button>
                <Button
                  data-testid="integrations-studio-conflict-submit"
                  disabled={conflictMutation.isPending}
                  onClick={async () => {
                    if (!selectedId) return;
                    try {
                      const rules = JSON.parse(rulesJson) as Array<{
                        internal: string;
                        winner: "source" | "salesos";
                        exclude_from_pull?: boolean;
                      }>;
                      if (!Array.isArray(rules)) {
                        throw new Error("rules must be a JSON array");
                      }
                      await conflictMutation.mutateAsync({
                        connectionId: selectedId,
                        body: {
                          rules,
                          salesos_authored_fields: listFromCsv(authoredCsv),
                          operational_fields: listFromCsv(operationalCsv),
                        },
                      });
                      toast({
                        variant: "success",
                        title: "Conflict policy saved",
                        description: selectedId,
                      });
                    } catch (err) {
                      toast({
                        variant: "error",
                        title: "Conflict policy failed",
                        description: getApiError(err),
                      });
                    }
                  }}
                >
                  {conflictMutation.isPending ? "Saving…" : "Save conflict policy"}
                </Button>
              </>
            )}
          </div>
        ) : null}

        {step === "schedule" ? (
          <div className="space-y-3" data-testid="integrations-studio-schedule">
            <div
              className="flex flex-wrap gap-2"
              data-testid="integrations-studio-schedule-model-presets"
            >
              {HUB_MODEL_PRESETS.map((preset) => (
                <Button
                  key={preset.id}
                  data-testid={`integrations-studio-schedule-preset-${preset.id}`}
                  onClick={() => applyModelPreset(preset.model)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            {isPartnerModel(model) ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-schedule-partner-hint"
              >
                Schedule model <code>res.partner</code> pulls company/contact partners (CR join in
                batch).
              </p>
            ) : null}
            {isOpportunityModel(model) ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-schedule-opportunity-hint"
              >
                Schedule model <code>crm.lead</code> pulls opportunities.
              </p>
            ) : null}
            {isNoteModel(model) ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-schedule-note-hint"
              >
                Schedule model <code>mail.message</code> pulls chatter notes (PII scrubbed).
              </p>
            ) : null}
            {isTicketModel(model) ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-schedule-ticket-hint"
              >
                Schedule model <code>helpdesk.ticket</code> pulls support tickets (strict stages +
                PII scrub).
              </p>
            ) : null}
            {isTaskModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-schedule-task-honesty"
              >
                Schedule model <code>project.task</code> pulls tasks with optional case extensions.
              </p>
            ) : null}
            {isInvoiceModel(model) ? (
              <p
                className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
                data-testid="integrations-studio-schedule-invoice-honesty"
              >
                Schedule model <code>account.move</code> pulls customer AR invoices (not platform
                Stripe billing).
              </p>
            ) : null}
            <Input
              label="Model"
              data-testid="integrations-studio-schedule-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
            <Input
              label="Schedule"
              data-testid="integrations-studio-schedule-cron"
              value={schedule}
              onChange={(e) => setSchedule(e.target.value)}
            />
            <Input
              label="Job name (optional tip ScheduleCreate.name)"
              data-testid="integrations-studio-schedule-name"
              value={scheduleName}
              onChange={(e) => setScheduleName(e.target.value)}
            />
            <label className="block text-xs text-[var(--text-muted)]">
              Job type (tip ScheduleCreate.job_type)
            </label>
            <select
              data-testid="integrations-studio-schedule-job-type"
              className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              value={scheduleJobType}
              onChange={(e) =>
                setScheduleJobType(e.target.value as "interval" | "cron" | "one_time")
              }
            >
              <option value="interval">interval</option>
              <option value="cron">cron</option>
              <option value="one_time">one_time</option>
            </select>
            <p className="text-xs text-[var(--text-muted)]">
              CAP-028 schedule string for interval (e.g. 15m) or cron expression.
            </p>
            <Button
              data-testid="integrations-studio-schedule-submit"
              disabled={!selectedId || scheduleMutation.isPending}
              onClick={async () => {
                if (!selectedId) return;
                try {
                  const result = await scheduleMutation.mutateAsync({
                    connectionId: selectedId,
                    body: {
                      model: model.trim(),
                      schedule: schedule.trim() || "15m",
                      job_type: scheduleJobType,
                      name: scheduleName.trim() || null,
                    },
                  });
                  setLastSchedule(result);
                  toast({
                    variant: "success",
                    title: "Sync scheduled",
                    description: `job ${result.job_id}`,
                  });
                } catch (err) {
                  toast({
                    variant: "error",
                    title: "Schedule failed",
                    description: getApiError(err),
                  });
                }
              }}
            >
              {scheduleMutation.isPending ? "Scheduling…" : "Schedule sync"}
            </Button>
            {lastSchedule ? (
              <p
                className="text-xs text-[var(--text-muted)]"
                data-testid="integrations-studio-schedule-result"
              >
                Last job {lastSchedule.job_id} · {lastSchedule.job_type} · {lastSchedule.schedule} ·
                next_run_at {lastSchedule.next_run_at || "n/a"}
              </p>
            ) : null}
          </div>
        ) : null}

        {step === "monitor" ? (
          <div className="space-y-3" data-testid="integrations-studio-monitor">
            <p
              className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
              data-testid="integrations-studio-unlinked-honesty"
            >
              Unlinked badges list partner-join residuals from sync runs — not a dedicated badge
              table.
            </p>
            <div className="space-y-2" data-testid="integrations-studio-unlinked-badges">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-medium">Unlinked badges</h3>
                <Button
                  data-testid="integrations-studio-unlinked-refresh"
                  disabled={!selectedId || unlinkedBadgesQuery.isFetching}
                  onClick={() => {
                    void unlinkedBadgesQuery.refetch();
                  }}
                >
                  {unlinkedBadgesQuery.isFetching ? "Refreshing…" : "Refresh badges"}
                </Button>
                <span
                  className="text-xs text-[var(--text-muted)]"
                  data-testid="integrations-studio-unlinked-count"
                >
                  {unlinkedBadgesQuery.isLoading
                    ? "Loading…"
                    : `${unlinkedBadgesQuery.data?.count ?? 0} badge(s)`}
                </span>
              </div>
              {!selectedId ? (
                <p className="text-sm text-[var(--text-muted)]">
                  Select a connection to list unlinked badges.
                </p>
              ) : unlinkedBadgesQuery.isLoading ? (
                <Spinner className="h-5 w-5" />
              ) : (unlinkedBadgesQuery.data?.items || []).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  No unlinked badges in recent SyncRun error_log.
                </p>
              ) : (
                <ul className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)] text-sm">
                  {(unlinkedBadgesQuery.data?.items || []).map((b) => (
                    <li
                      key={`${b.sync_run_id || "run"}-${b.external_id}-${b.status}`}
                      className="px-3 py-2"
                      data-testid="integrations-studio-unlinked-badge-row"
                    >
                      <span className="font-mono text-xs">{b.external_id}</span>
                      <span className="mx-2 text-[var(--text-muted)]">·</span>
                      <span>{b.status}</span>
                      {b.cr_number ? (
                        <>
                          <span className="mx-2 text-[var(--text-muted)]">·</span>
                          <span className="font-mono text-xs">cr {b.cr_number}</span>
                        </>
                      ) : null}
                      {b.message ? (
                        <p className="mt-1 text-xs text-[var(--text-muted)]">{b.message}</p>
                      ) : null}
                      {b.sync_run_id ? (
                        <p className="mt-0.5 font-mono text-[10px] text-[var(--text-disabled)]">
                          sync_run {b.sync_run_id}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <Button
              data-testid="integrations-studio-monitor-refresh"
              disabled={!selectedId || syncRunsQuery.isFetching}
              onClick={() => {
                void syncRunsQuery.refetch();
              }}
            >
              {syncRunsQuery.isFetching ? "Refreshing…" : "Refresh sync runs"}
            </Button>
            <div className="flex flex-wrap gap-3">
              <div>
                <label className="block text-xs text-[var(--text-muted)]">
                  Status filter (client-side on tip SyncRun rows)
                </label>
                <select
                  data-testid="integrations-studio-monitor-status-filter"
                  className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={monitorStatusFilter}
                  onChange={(e) => setMonitorStatusFilter(e.target.value)}
                >
                  <option value="all">All statuses</option>
                  <option value="success">success</option>
                  <option value="failed">failed</option>
                  <option value="running">running</option>
                  <option value="pending">pending</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)]">
                  Model filter (tip SyncRun.model)
                </label>
                <select
                  data-testid="integrations-studio-monitor-model-filter"
                  className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={monitorModelFilter}
                  onChange={(e) => setMonitorModelFilter(e.target.value)}
                >
                  <option value="all">All models</option>
                  {monitorModelOptions.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                  {HUB_MODEL_PRESETS.filter((p) => !monitorModelOptions.includes(p.model)).map(
                    (p) => (
                      <option key={p.id} value={p.model}>
                        {p.model}
                      </option>
                    )
                  )}
                </select>
              </div>
            </div>
            {!selectedId ? (
              <p className="text-sm text-[var(--text-muted)]">
                Select a connection to view SyncRun history.
              </p>
            ) : syncRunsQuery.isLoading ? (
              <Spinner className="h-5 w-5" />
            ) : (
              <ul
                className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
                data-testid="integrations-studio-sync-runs"
              >
                {filteredSyncRuns.length === 0 ? (
                  <li className="px-3 py-2 text-sm text-[var(--text-muted)]">No sync runs yet.</li>
                ) : (
                  filteredSyncRuns.map((run) => (
                    <li
                      key={run.id}
                      className="px-3 py-2 text-sm"
                      data-testid="integrations-studio-sync-run-row"
                    >
                      <span className="font-medium">{run.status}</span> · {run.model} · pulled{" "}
                      {run.records_pulled} / wrote {run.records_written} / failed{" "}
                      {run.records_failed}
                      <span className="mt-0.5 block text-xs text-[var(--text-muted)]">
                        started {run.started_at}
                        {run.finished_at ? ` · finished ${run.finished_at}` : ""}
                        {run.scheduled_job_id ? ` · job ${run.scheduled_job_id}` : ""}
                        {run.failure_class ? ` · ${run.failure_class}` : ""}
                      </span>
                      {syncRunHasCursors(run) ? (
                        <p
                          className="mt-1 text-[10px] text-[var(--text-muted)] break-all"
                          data-testid="integrations-studio-sync-run-cursors"
                        >
                          Cursors: {Object.keys(run.cursor_before || {}).length} before /{" "}
                          {Object.keys(run.cursor_after || {}).length} after
                        </p>
                      ) : null}
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs break-all">{run.id}</span>
                        <Button
                          data-testid="integrations-studio-copy-sync-run-id"
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(run.id);
                              toast({
                                variant: "success",
                                title: "SyncRun id copied",
                                description: run.id,
                              });
                            } catch {
                              toast({
                                variant: "error",
                                title: "Copy failed",
                                description: run.id,
                              });
                            }
                          }}
                        >
                          Copy run id
                        </Button>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>
        ) : null}

        {step === "disconnect" ? (
          <div className="space-y-3" data-testid="integrations-studio-disconnect">
            <p className="text-sm text-[var(--text-secondary)]">
              Deactivates the selected connection ({selected?.name || "none"}).
            </p>
            <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
              <input
                type="checkbox"
                data-testid="integrations-studio-disconnect-confirm"
                checked={disconnectConfirmed}
                onChange={(e) => setDisconnectConfirmed(e.target.checked)}
              />
              Confirm disconnect (deactivates connection; not a hard delete)
            </label>
            <Button
              variant="danger"
              data-testid="integrations-studio-disconnect-submit"
              disabled={!selectedId || !disconnectConfirmed || disconnectMutation.isPending}
              onClick={async () => {
                if (!selectedId) return;
                try {
                  const result = await disconnectMutation.mutateAsync(selectedId);
                  toast({
                    variant: "success",
                    title: "Disconnected",
                    description: result.message,
                  });
                  setSelectedId(null);
                  setDisconnectConfirmed(false);
                } catch (err) {
                  toast({
                    variant: "error",
                    title: "Disconnect failed",
                    description: getApiError(err),
                  });
                }
              }}
            >
              {disconnectMutation.isPending ? "Disconnecting…" : "Disconnect"}
            </Button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
