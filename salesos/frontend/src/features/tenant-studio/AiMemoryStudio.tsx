"use client";

import { useEffect, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAiMemoryConversation,
  useAiMemoryConversations,
  useAiMemoryMeta,
  useAiMemorySettings,
  useAppendAiMemoryTurn,
  useDeleteAiMemoryConversation,
  useProbeAiMemoryAdversarial,
  usePutAiMemorySettings,
} from "@/lib/hooks/aiMemoryStudioQueries";
import type { ConversationMemory } from "@/lib/api";
import {
  AI_MEMORY_HONESTY,
  AI_MEMORY_NON_GOALS,
} from "@/features/tenant-studio/aiMemoryHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S12-03 — AI Memory Studio (tip STORY-12-03).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 * Decision package remains STUB.
 */
export function AiMemoryStudio() {
  const { toast } = useToast();
  const metaQuery = useAiMemoryMeta();
  const settingsQuery = useAiMemorySettings();
  const listQuery = useAiMemoryConversations();
  const putSettings = usePutAiMemorySettings();
  const appendTurn = useAppendAiMemoryTurn();
  const deleteConv = useDeleteAiMemoryConversation();
  const probe = useProbeAiMemoryAdversarial();

  const [enabled, setEnabled] = useState(false);
  const [maxTurns, setMaxTurns] = useState("50");
  const [retentionHours, setRetentionHours] = useState("24");

  const [conversationId, setConversationId] = useState("demo-conv-1");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useAiMemoryConversation(selectedId);

  const [role, setRole] = useState("user");
  const [content, setContent] = useState("Hello from Studio probe.");
  const [probeResult, setProbeResult] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [ownerTenant, setOwnerTenant] = useState("tenant-a");
  const [attackerTenant, setAttackerTenant] = useState("tenant-b");
  const [probeConvId, setProbeConvId] = useState("demo-conv-1");

  useEffect(() => {
    if (!settingsQuery.data) return;
    setEnabled(Boolean(settingsQuery.data.enabled));
    setMaxTurns(String(settingsQuery.data.max_turns));
    setRetentionHours(String(settingsQuery.data.retention_hours));
  }, [settingsQuery.data]);

  const busy =
    putSettings.isPending ||
    appendTurn.isPending ||
    deleteConv.isPending ||
    probe.isPending;

  return (
    <div className="space-y-4" data-testid="ai-memory-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="ai-memory-honesty"
      >
        {AI_MEMORY_HONESTY} Non-goals: {AI_MEMORY_NON_GOALS.join("; ")}. Not
        Production GO / RAG GO.
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
          data-testid="ai-memory-meta"
        >
          <p>
            {metaQuery.data.capability} · scope={metaQuery.data.scope} ·
            cross_session={String(metaQuery.data.cross_session)} ·
            opt_in_default={String(metaQuery.data.opt_in_default)}
          </p>
          <p data-testid="ai-memory-meta-flag">
            feature_ai_copilot={String(metaQuery.data.feature_ai_copilot)}
          </p>
          <p data-testid="ai-memory-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
        </div>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-memory-settings"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Opt-in settings (tip GET/PUT /settings)
        </h2>
        {settingsQuery.isLoading ? (
          <Spinner />
        ) : (
          <>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                data-testid="ai-memory-enabled"
              />
              Enabled (opt-in)
            </label>
            <div className="flex flex-wrap gap-2">
              <Input
                value={maxTurns}
                onChange={(e) => setMaxTurns(e.target.value)}
                placeholder="max_turns"
                data-testid="ai-memory-max-turns"
              />
              <Input
                value={retentionHours}
                onChange={(e) => setRetentionHours(e.target.value)}
                placeholder="retention_hours"
                data-testid="ai-memory-retention"
              />
              <Button
                disabled={busy}
                data-testid="ai-memory-settings-save"
                onClick={() => {
                  putSettings.mutate(
                    {
                      enabled,
                      max_turns: Number(maxTurns) || 50,
                      retention_hours: Number(retentionHours) || 24,
                    },
                    {
                      onSuccess: () =>
                        toast({
                          title: "Settings saved",
                          variant: "success",
                        }),
                      onError: (err) =>
                        toast({
                          title: getApiError(err),
                          variant: "error",
                        }),
                    },
                  );
                }}
              >
                Save settings
              </Button>
            </div>
            {settingsQuery.data ? (
              <p
                className="font-mono text-xs text-[var(--text-muted)]"
                data-testid="ai-memory-settings-flag"
              >
                tip settings feature_ai_copilot=
                {String(settingsQuery.data.feature_ai_copilot)} · cross_session=
                {String(settingsQuery.data.cross_session)}
              </p>
            ) : null}
          </>
        )}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-memory-append"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Append turn (tip POST …/conversations/{"{id}"}/turns)
        </h2>
        <Input
          value={conversationId}
          onChange={(e) => setConversationId(e.target.value)}
          placeholder="conversation_id"
          data-testid="ai-memory-conversation-id"
        />
        <select
          className="rounded border border-[var(--border)] bg-transparent px-2 py-1 text-sm"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          data-testid="ai-memory-role"
        >
          <option value="user">user</option>
          <option value="assistant">assistant</option>
          <option value="system">system</option>
        </select>
        <Input
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="turn content"
          data-testid="ai-memory-content"
        />
        <Button
          disabled={busy || !conversationId.trim() || !content.trim()}
          data-testid="ai-memory-append-btn"
          onClick={() => {
            appendTurn.mutate(
              {
                conversationId: conversationId.trim(),
                body: { role, content: content.trim() },
              },
              {
                onSuccess: (row: ConversationMemory) => {
                  setSelectedId(row.conversation_id);
                  toast({
                    title: "Turn appended",
                    description: `turns=${row.turn_count}`,
                    variant: "success",
                  });
                },
                onError: (err) =>
                  toast({
                    title: getApiError(err),
                    variant: "error",
                  }),
              },
            );
          }}
        >
          Append turn
        </Button>
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-memory-list"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Conversations
          </h2>
          <Button
            variant="outline"
            size="sm"
            disabled={listQuery.isFetching}
            data-testid="ai-memory-refresh"
            onClick={() => listQuery.refetch()}
          >
            Refresh
          </Button>
        </div>
        {listQuery.isLoading ? (
          <Spinner />
        ) : listQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(listQuery.error)}
          </p>
        ) : (listQuery.data ?? []).length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="ai-memory-empty"
          >
            No conversation memories yet (enable opt-in, then append a turn).
          </p>
        ) : (
          <ul className="space-y-2">
            {(listQuery.data ?? []).map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-[var(--border)] px-3 py-2 text-sm"
                data-testid="ai-memory-row"
              >
                <div>
                  <p className="font-medium text-[var(--text-primary)]">
                    {row.conversation_id}
                  </p>
                  <p className="font-mono text-xs text-[var(--text-muted)]">
                    turns={row.turn_count} · cache={row.provider_cache_key}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    data-testid="ai-memory-open"
                    onClick={() => setSelectedId(row.conversation_id)}
                  >
                    Open
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    data-testid="ai-memory-delete"
                    onClick={() => {
                      deleteConv.mutate(row.conversation_id, {
                        onSuccess: () => {
                          if (selectedId === row.conversation_id) {
                            setSelectedId(null);
                          }
                          toast({
                            title: "Deleted",
                            variant: "success",
                          });
                        },
                        onError: (err) =>
                          toast({
                            title: getApiError(err),
                            variant: "error",
                          }),
                      });
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedId ? (
        <section
          className="space-y-2 rounded border border-[var(--border)] p-4"
          data-testid="ai-memory-detail"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Detail · {selectedId}
            </h2>
            <Button
              size="sm"
              variant="outline"
              data-testid="ai-memory-close"
              onClick={() => setSelectedId(null)}
            >
              Close
            </Button>
          </div>
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">
              {getApiError(detailQuery.error)}
            </p>
          ) : detailQuery.data ? (
            <pre
              className="overflow-auto rounded bg-[var(--surface-muted)] p-3 font-mono text-xs"
              data-testid="ai-memory-detail-result"
            >
              {JSON.stringify(detailQuery.data, null, 2)}
            </pre>
          ) : null}
        </section>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-memory-probe"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Adversarial probe (tip POST /adversarial/probe — no live LLM)
        </h2>
        <div className="flex flex-wrap gap-2">
          <Input
            value={ownerTenant}
            onChange={(e) => setOwnerTenant(e.target.value)}
            placeholder="owner_tenant_id"
            data-testid="ai-memory-probe-owner"
          />
          <Input
            value={attackerTenant}
            onChange={(e) => setAttackerTenant(e.target.value)}
            placeholder="attacker_tenant_id"
            data-testid="ai-memory-probe-attacker"
          />
          <Input
            value={probeConvId}
            onChange={(e) => setProbeConvId(e.target.value)}
            placeholder="conversation_id"
            data-testid="ai-memory-probe-conv"
          />
        </div>
        <Button
          disabled={busy}
          data-testid="ai-memory-probe-run"
          onClick={() => {
            probe.mutate(
              {
                owner_tenant_id: ownerTenant.trim(),
                attacker_tenant_id: attackerTenant.trim(),
                conversation_id: probeConvId.trim(),
              },
              {
                onSuccess: (result) => {
                  setProbeResult(result);
                  toast({ title: "Probe complete", variant: "success" });
                },
                onError: (err) =>
                  toast({
                    title: getApiError(err),
                    variant: "error",
                  }),
              },
            );
          }}
        >
          Run probe
        </Button>
        {probeResult ? (
          <pre
            className="overflow-auto rounded bg-[var(--surface-muted)] p-3 font-mono text-xs"
            data-testid="ai-memory-probe-result"
          >
            {JSON.stringify(probeResult, null, 2)}
          </pre>
        ) : null}
      </section>
    </div>
  );
}
