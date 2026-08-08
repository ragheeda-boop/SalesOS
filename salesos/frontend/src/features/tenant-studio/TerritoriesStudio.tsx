"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEffect, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAssignTerritory,
  useDeleteTerritoryRule,
  useTerritoriesMeta,
  useTerritoryRules,
  useUpsertTerritoryRule,
} from "@/lib/hooks/territoriesStudioQueries";
import type { TerritoryAssignResult, TerritoryRule } from "@/lib/api";
import {
  TERRITORIES_STUDIO_HONESTY,
  TERRITORIES_STUDIO_NON_GOALS,
} from "@/features/tenant-studio/territoriesStudioHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-05 — Territory Rules Studio against tip STORY-10-05 HTTP.
 * Not Production GO / RAG GO. TenantList untouched.
 */
export function TerritoriesStudio() {
  const { toast } = useToast();
  const metaQuery = useTerritoriesMeta();
  const listQuery = useTerritoryRules();
  const upsertMutation = useUpsertTerritoryRule();
  const deleteMutation = useDeleteTerritoryRule();
  const assignMutation = useAssignTerritory();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("Riyadh North");
  const [territoryKey, setTerritoryKey] = useState("riyadh-north");
  const [region, setRegion] = useState("Riyadh");
  const [repId, setRepId] = useState("rep-1");
  const [priority, setPriority] = useState("10");
  const [active, setActive] = useState(true);
  const [matchField, setMatchField] = useState("region");
  const [matchOp, setMatchOp] = useState("eq");
  const [matchValue, setMatchValue] = useState("Riyadh");
  const [assignJson, setAssignJson] = useState('{\n  "region": "Riyadh",\n  "industry": "gov"\n}');
  const [lastAssign, setLastAssign] = useState<TerritoryAssignResult | null>(null);

// eslint-disable-next-line react-hooks/exhaustive-deps
  const fields = metaQuery.data?.match_fields ?? ["region", "industry", "employee_count"];
  const ops = metaQuery.data?.match_ops ?? ["eq", "gte", "contains"];

  useEffect(() => {
    if (!fields.includes(matchField) && fields[0]) {
      setMatchField(fields[0]);
    }
  }, [fields, matchField]);

  function loadRule(row: TerritoryRule) {
    setSelectedId(row.id);
    setName(row.name);
    setTerritoryKey(row.territory_key);
    setRegion(row.region || "");
    setRepId(row.rep_id || "");
    setPriority(String(row.priority));
    setActive(row.active);
    const c0 = row.match_conditions[0];
    if (c0) {
      setMatchField(c0.field);
      setMatchOp(c0.op);
      setMatchValue(
        typeof c0.value === "string" || typeof c0.value === "number"
          ? String(c0.value)
          : JSON.stringify(c0.value ?? "")
      );
    }
  }

  function parseMatchValue(raw: string): unknown {
    const trimmed = raw.trim();
    if (trimmed === "") return "";
    if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
    if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
      try {
        return JSON.parse(trimmed) as unknown;
      } catch {
        return trimmed;
      }
    }
    return trimmed;
  }

  return (
    <div className="space-y-4" data-testid="territories-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="territories-studio-honesty"
      >
        {TERRITORIES_STUDIO_HONESTY} Non-goals: {TERRITORIES_STUDIO_NON_GOALS.join("; ")}. Not
        Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <p
          className="font-mono text-xs text-[var(--text-muted)]"
          data-testid="territories-studio-meta"
        >
          runtime={metaQuery.data.runtime} · persistence=
          {metaQuery.data.persistence} · dimensions=
          {metaQuery.data.dimensions.join(",")} · fields=
          {metaQuery.data.match_fields.join(",")}
        </p>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : (
        <Spinner />
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          data-testid="territories-studio-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh rules"}
        </Button>
        <span className="text-sm text-[var(--text-muted)]" data-testid="territories-studio-count">
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">{getApiError(listQuery.error)}</span>
          ) : (
            <>{listQuery.data?.length ?? 0} rule(s)</>
          )}
        </span>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          data-testid="territories-studio-new"
          onClick={() => {
            setSelectedId(null);
            setName("Riyadh North");
            setTerritoryKey("riyadh-north");
            setRegion("Riyadh");
            setRepId("rep-1");
            setPriority("10");
            setActive(true);
            setMatchField("region");
            setMatchOp("eq");
            setMatchValue("Riyadh");
          }}
        >
          New rule
        </Button>
      </div>

      <ul
        className="max-h-48 divide-y divide-[var(--border-default)] overflow-y-auto rounded border border-[var(--border-default)]"
        data-testid="territories-studio-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No territory rules yet. Upsert one below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li key={row.id} className="flex items-center gap-2 px-3 py-2">
              <button
                type="button"
                className={`flex-1 text-left text-sm hover:underline ${
                  selectedId === row.id ? "font-medium" : ""
                }`}
                data-testid="territories-studio-row"
                onClick={() => loadRule(row)}
              >
                {row.name} · {row.territory_key} · p{row.priority}
                {!row.active ? " · inactive" : ""}
              </button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                data-testid="territories-studio-delete"
                disabled={deleteMutation.isPending}
                onClick={() => {
                  deleteMutation.mutate(row.id, {
                    onSuccess: () => {
                      if (selectedId === row.id) setSelectedId(null);
                      toast({
                        title: "Deleted",
                        description: row.id,
                        variant: "success",
                      });
                    },
                    onError: (err) => {
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
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="territories-studio-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim() || !territoryKey.trim() || !matchValue.trim()) {
            toast({
              title: "Rule required",
              description: "name, territory_key, and match value required.",
              variant: "error",
            });
            return;
          }
          upsertMutation.mutate(
            {
              ...(selectedId ? { id: selectedId } : {}),
              name: name.trim(),
              territory_key: territoryKey.trim(),
              region: region.trim(),
              rep_id: repId.trim(),
              priority: Number(priority) || 100,
              active,
              match_conditions: [
                {
                  field: matchField,
                  op: matchOp,
                  value: parseMatchValue(matchValue),
                },
              ],
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  title: "Territory rule saved",
                  description: row.territory_key,
                  variant: "success",
                });
              },
              onError: (err) => {
                toast({
                  title: "Save failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold">
          {selectedId ? "Update rule (tip POST id=)" : "Create rule (tip POST)"}
        </h2>
        <Input
          label="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          data-testid="territories-studio-name"
        />
        <Input
          label="territory_key"
          value={territoryKey}
          onChange={(e) => setTerritoryKey(e.target.value)}
          data-testid="territories-studio-key"
        />
        <Input
          label="region"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          data-testid="territories-studio-region"
        />
        <Input
          label="rep_id"
          value={repId}
          onChange={(e) => setRepId(e.target.value)}
          data-testid="territories-studio-rep"
        />
        <Input
          label="priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="max-w-[8rem]"
          data-testid="territories-studio-priority"
        />
        <label className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
          <input
            type="checkbox"
            checked={active}
            onChange={(e) => setActive(e.target.checked)}
            data-testid="territories-studio-active"
          />
          active
        </label>
        <div className="grid gap-2 md:grid-cols-3">
          <label className="block text-xs text-[var(--text-muted)]">
            match field
            <select
              className="mt-1 w-full rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 text-sm"
              value={matchField}
              onChange={(e) => setMatchField(e.target.value)}
              data-testid="territories-studio-match-field"
            >
              {fields.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs text-[var(--text-muted)]">
            match op
            <select
              className="mt-1 w-full rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 text-sm"
              value={matchOp}
              onChange={(e) => setMatchOp(e.target.value)}
              data-testid="territories-studio-match-op"
            >
              {ops.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="match value"
            value={matchValue}
            onChange={(e) => setMatchValue(e.target.value)}
            data-testid="territories-studio-match-value"
          />
        </div>
        <Button
          type="submit"
          disabled={upsertMutation.isPending}
          data-testid="territories-studio-save"
        >
          {upsertMutation.isPending ? "Saving…" : "Save rule"}
        </Button>
      </form>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="territories-studio-assign-form"
        onSubmit={(e) => {
          e.preventDefault();
          let attributes: Record<string, unknown>;
          try {
            attributes = JSON.parse(assignJson) as Record<string, unknown>;
            if (
              attributes === null ||
              typeof attributes !== "object" ||
              Array.isArray(attributes)
            ) {
              throw new Error("attributes must be a JSON object");
            }
          } catch (err) {
            toast({
              title: "Invalid attributes JSON",
              description: getApiError(err),
              variant: "error",
            });
            return;
          }
          assignMutation.mutate(
            {
              attributes,
              ...(selectedId ? { rule_id: selectedId } : {}),
            },
            {
              onSuccess: (row) => {
                setLastAssign(row);
                toast({
                  title: row.matched ? "Matched" : "Unmatched",
                  description: row.matched
                    ? `${row.territory_key} · ${row.source}`
                    : `source=${row.source} (no invented key)`,
                  variant: row.matched ? "success" : "error",
                });
              },
              onError: (err) => {
                toast({
                  title: "Assign failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold">Assign (tip POST /assign)</h2>
        <label className="block text-xs text-[var(--text-muted)]">
          attributes JSON
          <textarea
            className="mt-1 min-h-[88px] w-full rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 font-mono text-xs"
            value={assignJson}
            onChange={(e) => setAssignJson(e.target.value)}
            data-testid="territories-studio-assign-json"
          />
        </label>
        <Button
          type="submit"
          disabled={assignMutation.isPending}
          data-testid="territories-studio-assign"
        >
          {assignMutation.isPending ? "Assigning…" : "Assign"}
        </Button>
        {lastAssign ? (
          <pre
            className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
            data-testid="territories-studio-assign-result"
          >
            {JSON.stringify(lastAssign, null, 2)}
          </pre>
        ) : null}
      </form>
    </div>
  );
}
