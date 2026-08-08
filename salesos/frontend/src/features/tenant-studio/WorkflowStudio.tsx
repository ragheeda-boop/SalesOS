"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCompileWorkflowCanvas,
  useCompileWorkflowCanvasEphemeral,
  useUpsertWorkflowCanvas,
  useWorkflowCanvases,
} from "@/lib/hooks/workflowStudioQueries";
import type { WorkflowCanvasNode } from "@/lib/api/types/tenantStudio";
import { WORKFLOW_ACTION_STEP_TYPES } from "@/lib/api/types/tenantStudio";
import {
  WORKFLOW_STUDIO_HONESTY,
  WORKFLOW_STUDIO_NON_GOALS,
} from "@/features/tenant-studio/workflowStudioHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

const DEFAULT_NODES_JSON = JSON.stringify(
  [
    {
      id: "n1",
      kind: "action",
      step_type: "log_message",
      config: { message: "hello from Studio canvas" },
    },
    {
      id: "n2",
      kind: "action",
      step_type: "create_task",
      config: { title: "Follow up" },
    },
  ],
  null,
  2
);

/**
 * FE-S10-03 — Workflow Builder Studio against tip STORY-10-03 HTTP.
 * Canvas → WorkflowEngine compile. Not Production GO / RAG GO.
 * TenantList untouched. for_each not invented.
 */
export function WorkflowStudio() {
  const { toast } = useToast();
  const listQuery = useWorkflowCanvases();
  const upsertMutation = useUpsertWorkflowCanvas();
  const compileMutation = useCompileWorkflowCanvas();
  const ephemeralMutation = useCompileWorkflowCanvasEphemeral();

  const [name, setName] = useState("Studio canvas");
  const [description, setDescription] = useState("");
  const [triggerType, setTriggerType] = useState("manual");
  const [nodesJson, setNodesJson] = useState(DEFAULT_NODES_JSON);
  const [selectedId, setSelectedId] = useState("");

  function parseNodes(): WorkflowCanvasNode[] | null {
    try {
      const raw = JSON.parse(nodesJson) as WorkflowCanvasNode[];
      if (!Array.isArray(raw)) throw new Error("nodes must be an array");
      return raw;
    } catch (err) {
      toast({
        variant: "error",
        title: "Invalid nodes JSON",
        description: err instanceof Error ? err.message : "parse failed",
      });
      return null;
    }
  }

  return (
    <div className="space-y-4" data-testid="workflow-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="workflow-studio-honesty"
      >
        {WORKFLOW_STUDIO_HONESTY} Non-goals: {WORKFLOW_STUDIO_NON_GOALS.join("; ")}. Not Production
        GO / RAG GO.
      </p>

      <p className="text-xs text-[var(--text-muted)]" data-testid="workflow-action-types">
        Allowed action step_types: {WORKFLOW_ACTION_STEP_TYPES.join(", ")}. Use kind=branch for
        if_else (for_each rejected on tip).
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="workflow-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh canvases"}
        </Button>
        <span className="text-sm text-[var(--text-muted)]" data-testid="workflow-count">
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">{getApiError(listQuery.error)}</span>
          ) : (
            <>{listQuery.data?.length ?? 0} canvas(es)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="workflow-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No canvases yet. Upsert one below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li
              key={row.id}
              className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
              data-testid="workflow-row"
            >
              <span>
                <span className="font-medium">{row.name}</span> · {row.trigger_type} ·{" "}
                {row.nodes?.length ?? 0} node(s)
                <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                  {row.id}
                </span>
              </span>
              <Button
                data-testid={`workflow-compile-${row.id}`}
                disabled={compileMutation.isPending}
                onClick={() => {
                  setSelectedId(row.id);
                  compileMutation.mutate(row.id, {
                    onSuccess: () => {
                      toast({
                        variant: "success",
                        title: "Compiled",
                        description: row.id,
                      });
                    },
                    onError: (err) => {
                      toast({
                        variant: "error",
                        title: "Compile failed",
                        description: getApiError(err),
                      });
                    },
                  });
                }}
              >
                Compile
              </Button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="workflow-upsert-form"
        onSubmit={(e) => {
          e.preventDefault();
          const nodes = parseNodes();
          if (!nodes) return;
          upsertMutation.mutate(
            {
              name: name.trim(),
              description: description.trim(),
              trigger_type: triggerType.trim() || "manual",
              nodes,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  variant: "success",
                  title: "Canvas saved",
                  description: `${row.name} (${row.id})`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Upsert failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Upsert canvas (tip POST)
        </h2>
        <Input
          label="name"
          data-testid="workflow-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          label="description"
          data-testid="workflow-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Input
          label="trigger_type"
          data-testid="workflow-trigger-type"
          value={triggerType}
          onChange={(e) => setTriggerType(e.target.value)}
        />
        <div>
          <label className="block text-xs text-[var(--text-muted)]">nodes (JSON)</label>
          <textarea
            data-testid="workflow-nodes-json"
            className="min-h-[160px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs"
            value={nodesJson}
            onChange={(e) => setNodesJson(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="submit"
            data-testid="workflow-submit"
            disabled={upsertMutation.isPending || !name.trim()}
          >
            {upsertMutation.isPending ? "Saving…" : "Save canvas"}
          </Button>
          <Button
            type="button"
            data-testid="workflow-compile-ephemeral"
            disabled={ephemeralMutation.isPending}
            onClick={() => {
              const nodes = parseNodes();
              if (!nodes) return;
              ephemeralMutation.mutate(
                {
                  name: name.trim() || "ephemeral",
                  description: description.trim(),
                  trigger_type: triggerType.trim() || "manual",
                  nodes,
                },
                {
                  onSuccess: () => {
                    toast({
                      variant: "success",
                      title: "Ephemeral compile ok",
                    });
                  },
                  onError: (err) => {
                    toast({
                      variant: "error",
                      title: "Ephemeral compile failed",
                      description: getApiError(err),
                    });
                  },
                }
              );
            }}
          >
            {ephemeralMutation.isPending ? "Compiling…" : "Compile unsaved (tip POST …/compile)"}
          </Button>
        </div>
      </form>

      {(compileMutation.data || ephemeralMutation.data) && (
        <pre
          className="overflow-auto rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-[10px] text-[var(--text-muted)]"
          data-testid="workflow-compile-result"
        >
          {JSON.stringify(compileMutation.data || ephemeralMutation.data, null, 2)}
        </pre>
      )}
      {selectedId ? (
        <p className="text-xs text-[var(--text-muted)]" data-testid="workflow-selected-id">
          Selected canvas: {selectedId}
        </p>
      ) : null}
    </div>
  );
}
