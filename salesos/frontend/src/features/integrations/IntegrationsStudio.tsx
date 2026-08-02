"use client";

import { useMemo, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCreateHubConnection,
  useCreateHubMapping,
  useDisconnectHubConnection,
  useHubConnections,
  useHubSyncRuns,
  useScheduleHubSync,
  useTestHubConnection,
} from "@/lib/hooks/integrationHubQueries";
import { STUDIO_STEPS } from "@/features/admin/IntegrationsStudioShell";
import type { HubConnection } from "@/lib/api";

export type StudioStepId = (typeof STUDIO_STEPS)[number]["id"];

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * STORY-08-07 — Integrations Studio against Hub HTTP (STORY-08-06).
 * Connect / test / map / schedule / monitor / disconnect. Fake adapter only
 * for test_connection until Odoo GA. Not Production GO. No invented secrets.
 */
export function IntegrationsStudio() {
  const { toast } = useToast();
  const [step, setStep] = useState<StudioStepId>("connect");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("Fake connector");
  const [connectorKey, setConnectorKey] = useState("fake");
  const [credentialRef, setCredentialRef] = useState("vault:demo/fake");
  const [model, setModel] = useState("company");
  const [mappingJson, setMappingJson] = useState(
    '[{"external":"name","internal":"name"}]',
  );
  const [schedule, setSchedule] = useState("15m");
  const [lastTest, setLastTest] = useState<string>("");

  const connectionsQuery = useHubConnections();
  const syncRunsQuery = useHubSyncRuns(selectedId);
  const createMutation = useCreateHubConnection();
  const testMutation = useTestHubConnection();
  const mapMutation = useCreateHubMapping();
  const scheduleMutation = useScheduleHubSync();
  const disconnectMutation = useDisconnectHubConnection();

  const connections = connectionsQuery.data || [];
  const selected: HubConnection | undefined = useMemo(
    () => connections.find((c) => c.id === selectedId),
    [connections, selectedId],
  );

  const needsConnection = step !== "connect";

  return (
    <div className="space-y-4" data-testid="integrations-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="integrations-studio-live-honesty"
      >
        STORY-08-07 Studio wired to `/api/v1/integrations/*` (STORY-08-06).
        DOM-021 entitlement gated. `test_connection` uses FakeSourceConnector
        until Odoo adapter GA. Do not paste real secrets into credential_ref in
        demos. Not Production GO.
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
            <label className="block text-xs text-[var(--text-muted)]">
              Connection
            </label>
            {connectionsQuery.isLoading ? (
              <Spinner className="h-5 w-5" />
            ) : (
              <select
                data-testid="integrations-studio-connection-select"
                className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={selectedId || ""}
                onChange={(e) => setSelectedId(e.target.value || null)}
              >
                <option value="">Select a connection…</option>
                {connections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.connector_key})
                    {c.is_active ? "" : " · inactive"}
                  </option>
                ))}
              </select>
            )}
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
              Use connector key <code>fake</code> until Odoo adapter GA.
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
            <Button
              data-testid="integrations-studio-connect-submit"
              disabled={createMutation.isPending}
              onClick={async () => {
                try {
                  const row = await createMutation.mutateAsync({
                    name: name.trim(),
                    connector_key: connectorKey.trim(),
                    credential_ref: credentialRef.trim(),
                    connection_config: {},
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
              Runs FakeSourceConnector.test_connection for the selected row.
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
            <Input
              label="Model"
              data-testid="integrations-studio-map-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
            <label className="block text-xs text-[var(--text-muted)]">
              Mappings JSON
            </label>
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
                  const mappings = JSON.parse(mappingJson) as Record<
                    string,
                    unknown
                  >[];
                  if (!Array.isArray(mappings)) {
                    throw new Error("mappings must be a JSON array");
                  }
                  await mapMutation.mutateAsync({
                    connectionId: selectedId,
                    body: { model: model.trim(), mappings, version: 1 },
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

        {step === "schedule" ? (
          <div className="space-y-3" data-testid="integrations-studio-schedule">
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
            <p className="text-xs text-[var(--text-muted)]">
              CAP-028 interval string, e.g. 15m.
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
                      job_type: "interval",
                    },
                  });
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
          </div>
        ) : null}

        {step === "monitor" ? (
          <div className="space-y-3" data-testid="integrations-studio-monitor">
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
                {(syncRunsQuery.data || []).length === 0 ? (
                  <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
                    No sync runs yet.
                  </li>
                ) : (
                  (syncRunsQuery.data || []).map((run) => (
                    <li
                      key={run.id}
                      className="px-3 py-2 text-sm"
                      data-testid="integrations-studio-sync-run-row"
                    >
                      <span className="font-medium">{run.status}</span> ·{" "}
                      {run.model} · pulled {run.records_pulled} / wrote{" "}
                      {run.records_written} / failed {run.records_failed}
                      <span className="mt-0.5 block text-xs text-[var(--text-muted)]">
                        {run.started_at}
                        {run.failure_class ? ` · ${run.failure_class}` : ""}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>
        ) : null}

        {step === "disconnect" ? (
          <div
            className="space-y-3"
            data-testid="integrations-studio-disconnect"
          >
            <p className="text-sm text-[var(--text-secondary)]">
              Deactivates the selected connection ({selected?.name || "none"}).
            </p>
            <Button
              variant="danger"
              data-testid="integrations-studio-disconnect-submit"
              disabled={!selectedId || disconnectMutation.isPending}
              onClick={async () => {
                if (!selectedId) return;
                try {
                  const result =
                    await disconnectMutation.mutateAsync(selectedId);
                  toast({
                    variant: "success",
                    title: "Disconnected",
                    description: result.message,
                  });
                  setSelectedId(null);
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
