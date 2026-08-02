"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAddPromptLibraryVersion,
  useCreatePromptLibraryEntry,
  useDeletePromptLibraryEntry,
  usePromptLibraryDetail,
  usePromptLibraryList,
  usePromptLibraryMeta,
  useRollbackPromptLibrary,
} from "@/lib/hooks/promptLibraryQueries";
import type { PromptLibraryEntry } from "@/lib/api";
import {
  PROMPT_LIBRARY_HONESTY,
  PROMPT_LIBRARY_NON_GOALS,
} from "@/features/tenant-studio/promptLibraryHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S12-01 — Prompt Library Studio (tip STORY-12-01).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 */
export function PromptLibraryStudio() {
  const { toast } = useToast();
  const metaQuery = usePromptLibraryMeta();
  const listQuery = usePromptLibraryList();
  const createMutation = useCreatePromptLibraryEntry();
  const versionMutation = useAddPromptLibraryVersion();
  const rollbackMutation = useRollbackPromptLibrary();
  const deleteMutation = useDeletePromptLibraryEntry();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = usePromptLibraryDetail(selectedId);

  const [name, setName] = useState("GTM Intro Prompt");
  const [key, setKey] = useState("gtm.intro.v1");
  const [template, setTemplate] = useState(
    "Write a short intro for {{company_name}}.",
  );
  const [system, setSystem] = useState("");
  const [domain, setDomain] = useState("gtm");
  const [category, setCategory] = useState("general");

  const [newVersion, setNewVersion] = useState("1.0.1");
  const [newTemplate, setNewTemplate] = useState("");
  const [newChangelog, setNewChangelog] = useState("iteration");
  const [rollbackVersion, setRollbackVersion] = useState("");

  const busy =
    createMutation.isPending ||
    versionMutation.isPending ||
    rollbackMutation.isPending ||
    deleteMutation.isPending;

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="prompt-library-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="prompt-library-honesty"
      >
        {PROMPT_LIBRARY_HONESTY} Non-goals:{" "}
        {PROMPT_LIBRARY_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
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
          data-testid="prompt-library-meta"
        >
          <p>
            {metaQuery.data.capability} · extends={metaQuery.data.extends} ·
            ops={(metaQuery.data.operations ?? []).join(", ")}
          </p>
          <p data-testid="prompt-library-meta-flag">
            feature_ai_copilot={String(metaQuery.data.feature_ai_copilot)}
          </p>
          <p data-testid="prompt-library-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
        </div>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="prompt-library-create"
      >
        <h2 className="text-sm font-semibold">Create prompt (tip POST)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="max-w-xs"
            data-testid="prompt-library-name"
          />
          <Input
            label="key"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            className="max-w-xs"
            data-testid="prompt-library-key"
          />
          <Input
            label="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="max-w-xs"
            data-testid="prompt-library-domain"
          />
          <Input
            label="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="max-w-xs"
            data-testid="prompt-library-category"
          />
          <Input
            label="system (optional)"
            value={system}
            onChange={(e) => setSystem(e.target.value)}
            className="min-w-[12rem] flex-1"
            data-testid="prompt-library-system"
          />
          <Input
            label="template"
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="min-w-[16rem] flex-1"
            data-testid="prompt-library-template"
          />
          <Button
            type="button"
            size="sm"
            data-testid="prompt-library-create-btn"
            disabled={busy || !name.trim() || !key.trim() || !template.trim()}
            onClick={() => {
              createMutation.mutate(
                {
                  name: name.trim(),
                  key: key.trim(),
                  template: template.trim(),
                  system: system.trim() || undefined,
                  domain: domain.trim() || "gtm",
                  category: category.trim() || "general",
                },
                {
                  onSuccess: (row: PromptLibraryEntry) => {
                    setSelectedId(row.id);
                    toast({
                      title: "Prompt created",
                      description: `${row.key} @ ${row.active_version}`,
                    });
                  },
                  onError: (err: unknown) => {
                    toast({
                      title: "Create failed",
                      description: getApiError(err),
                      variant: "error",
                    });
                  },
                },
              );
            }}
          >
            {createMutation.isPending ? "Creating…" : "Create"}
          </Button>
        </div>
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="prompt-library-list"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">Library (tip GET)</h2>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            data-testid="prompt-library-refresh"
            onClick={() => {
              void metaQuery.refetch();
              void listQuery.refetch();
            }}
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
        ) : listQuery.data?.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="prompt-library-empty"
          >
            No prompts in memory library yet.
          </p>
        ) : (
          <ul className="space-y-2 text-sm">
            {(listQuery.data ?? []).map((row: PromptLibraryEntry) => (
              <li
                key={row.id}
                className="rounded border border-[var(--border-default)] px-3 py-2"
                data-testid="prompt-library-row"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-medium">{row.name}</span>{" "}
                    <span className="font-mono text-xs text-[var(--text-muted)]">
                      {row.key} · active={row.active_version} · versions=
                      {row.version_count} · {row.domain}/{row.category}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      data-testid="prompt-library-open"
                      onClick={() => {
                        setSelectedId(row.id);
                        setRollbackVersion(row.active_version);
                        setNewTemplate(
                          row.versions.find(
                            (v) => v.version === row.active_version,
                          )?.template ?? "",
                        );
                      }}
                    >
                      Open
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      data-testid="prompt-library-delete"
                      disabled={busy}
                      onClick={() => {
                        deleteMutation.mutate(row.id, {
                          onSuccess: () => {
                            if (selectedId === row.id) setSelectedId(null);
                            toast({ title: "Deleted", description: row.key });
                          },
                          onError: (err: unknown) => {
                            toast({
                              title: "Delete failed",
                              description: getApiError(err),
                              variant: "error",
                            });
                          },
                        });
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedId ? (
        <section
          className="space-y-3 rounded border border-[var(--border-default)] p-4"
          data-testid="prompt-library-detail"
        >
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">
              Detail / version / rollback
            </h2>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              data-testid="prompt-library-close"
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
          ) : active ? (
            <>
              <p className="font-mono text-xs text-[var(--text-muted)]">
                {active.key} · active={active.active_version} · versions=
                {active.versions.map((v) => v.version).join(", ")}
              </p>
              <div className="flex flex-wrap items-end gap-2">
                <Input
                  label="new version"
                  value={newVersion}
                  onChange={(e) => setNewVersion(e.target.value)}
                  className="max-w-xs"
                  data-testid="prompt-library-new-version"
                />
                <Input
                  label="changelog"
                  value={newChangelog}
                  onChange={(e) => setNewChangelog(e.target.value)}
                  className="max-w-xs"
                  data-testid="prompt-library-changelog"
                />
                <Input
                  label="template"
                  value={newTemplate}
                  onChange={(e) => setNewTemplate(e.target.value)}
                  className="min-w-[16rem] flex-1"
                  data-testid="prompt-library-new-template"
                />
                <Button
                  type="button"
                  size="sm"
                  data-testid="prompt-library-add-version"
                  disabled={busy || !newVersion.trim() || !newTemplate.trim()}
                  onClick={() => {
                    versionMutation.mutate(
                      {
                        entryId: active.id,
                        body: {
                          version: newVersion.trim(),
                          template: newTemplate.trim(),
                          changelog: newChangelog.trim() || undefined,
                          activate: true,
                        },
                      },
                      {
                        onSuccess: (row: PromptLibraryEntry) => {
                          toast({
                            title: "Version added",
                            description: `active=${row.active_version}`,
                          });
                        },
                        onError: (err: unknown) => {
                          toast({
                            title: "Version failed",
                            description: getApiError(err),
                            variant: "error",
                          });
                        },
                      },
                    );
                  }}
                >
                  Add version
                </Button>
              </div>
              <div className="flex flex-wrap items-end gap-2">
                <Input
                  label="rollback to version"
                  value={rollbackVersion}
                  onChange={(e) => setRollbackVersion(e.target.value)}
                  className="max-w-xs"
                  data-testid="prompt-library-rollback-version"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="prompt-library-rollback"
                  disabled={busy || !rollbackVersion.trim()}
                  onClick={() => {
                    rollbackMutation.mutate(
                      {
                        entryId: active.id,
                        body: { version: rollbackVersion.trim() },
                      },
                      {
                        onSuccess: (row: PromptLibraryEntry) => {
                          toast({
                            title: "Rolled back",
                            description: `active=${row.active_version}`,
                          });
                        },
                        onError: (err: unknown) => {
                          toast({
                            title: "Rollback failed",
                            description: getApiError(err),
                            variant: "error",
                          });
                        },
                      },
                    );
                  }}
                >
                  Rollback
                </Button>
              </div>
              <pre
                className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
                data-testid="prompt-library-detail-result"
              >
                {JSON.stringify(active, null, 2)}
              </pre>
            </>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
