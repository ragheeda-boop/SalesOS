"use client";

import { useEffect, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCustomFieldsFormSchema,
  useProjectCustomFieldValues,
} from "@/lib/hooks/tenantStudioQueries";
import type {
  AutoRenderFormField,
  StudioObjectKey,
} from "@/lib/api/types/tenantStudio";
import { CUSTOM_FIELDS_AUTO_RENDER_HONESTY } from "@/features/tenant-studio/customFieldsHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

function renderAutoField(
  field: AutoRenderFormField,
  value: unknown,
  onChange: (key: string, next: string) => void,
) {
  if (field.visible === false) return null;
  const str = value == null ? "" : String(value);
  if (field.type === "enum" && field.enum?.length) {
    return (
      <div key={field.key}>
        <label className="block text-xs text-[var(--text-muted)]">
          {field.label}
        </label>
        <select
          data-testid={`custom-fields-auto-input-${field.key}`}
          className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
          value={str}
          disabled={field.disabled}
          onChange={(e) => onChange(field.key, e.target.value)}
        >
          <option value="">—</option>
          {field.enum.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }
  return (
    <Input
      key={field.key}
      label={field.label}
      data-testid={`custom-fields-auto-input-${field.key}`}
      type={
        field.type === "number"
          ? "number"
          : field.type === "date"
            ? "date"
            : "text"
      }
      value={str}
      disabled={field.disabled}
      onChange={(e) => onChange(field.key, e.target.value)}
    />
  );
}

/**
 * FE-S10-02 — Generic auto-render from tip GET .../form-schema.
 * Zero per-field frontend code. POST .../values projects metadata.custom_fields
 * (no ORM write / no Postgres claim). Not Production GO / RAG GO.
 */
export function CustomFieldsAutoRender({
  objectKey,
  initialMetadata,
}: {
  objectKey: StudioObjectKey;
  initialMetadata?: Record<string, unknown>;
}) {
  const { toast } = useToast();
  const formQuery = useCustomFieldsFormSchema(objectKey);
  const projectMutation = useProjectCustomFieldValues(objectKey);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [projectedMeta, setProjectedMeta] = useState<Record<
    string,
    unknown
  > | null>(null);

  useEffect(() => {
    if (formQuery.data?.values) {
      setValues({ ...formQuery.data.values });
    }
  }, [formQuery.data?.id, formQuery.data?.schema_version]);

  const fields = formQuery.data?.fields ?? [];

  return (
    <section
      className="space-y-3 rounded border border-[var(--border-default)] p-3"
      data-testid="custom-fields-auto-render"
      data-object-key={objectKey}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Custom fields
        </h2>
        <Button
          data-testid="custom-fields-auto-refresh"
          disabled={formQuery.isFetching}
          onClick={() => {
            void formQuery.refetch();
          }}
        >
          {formQuery.isFetching ? "Refreshing…" : "Refresh form-schema"}
        </Button>
      </div>

      <p
        className="rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-muted)]"
        data-testid="custom-fields-auto-honesty"
      >
        {CUSTOM_FIELDS_AUTO_RENDER_HONESTY} Not Production GO / RAG GO.
      </p>

      {formQuery.isLoading ? (
        <Spinner className="h-5 w-5" />
      ) : formQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">
          {getApiError(formQuery.error)}
        </p>
      ) : fields.length === 0 ? (
        <p
          className="text-sm text-[var(--text-muted)]"
          data-testid="custom-fields-auto-empty"
        >
          No custom fields defined for {objectKey}. Define them at{" "}
          <code>/studio/custom-fields</code>.
        </p>
      ) : (
        <>
          <p
            className="text-xs text-[var(--text-muted)]"
            data-testid="custom-fields-auto-meta"
          >
            {formQuery.data?.title} · schema_version{" "}
            {formQuery.data?.schema_version} · renderer{" "}
            {formQuery.data?.renderer} · bag {formQuery.data?.bag_key}
          </p>
          <div
            className="grid gap-3 sm:grid-cols-2"
            data-testid="custom-fields-auto-fields"
          >
            {fields.map((field) =>
              renderAutoField(field, values[field.key], (key, next) => {
                setValues((prev) => ({ ...prev, [key]: next }));
              }),
            )}
          </div>
          <Button
            data-testid="custom-fields-auto-project"
            disabled={projectMutation.isPending}
            onClick={() => {
              projectMutation.mutate(
                {
                  values,
                  metadata: initialMetadata || projectedMeta || {},
                },
                {
                  onSuccess: (row) => {
                    setValues(row.values);
                    setProjectedMeta(row.metadata);
                    toast({
                      variant: "success",
                      title: "Values projected",
                      description: `metadata.${row.bag_key} (tip POST — no ORM write)`,
                    });
                  },
                  onError: (err) => {
                    toast({
                      variant: "error",
                      title: "Project failed",
                      description: getApiError(err),
                    });
                  },
                },
              );
            }}
          >
            {projectMutation.isPending
              ? "Projecting…"
              : "Project values (tip POST)"}
          </Button>
          {projectedMeta ? (
            <pre
              className="overflow-auto rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-[10px] text-[var(--text-muted)]"
              data-testid="custom-fields-auto-projected-meta"
            >
              {JSON.stringify(projectedMeta, null, 2)}
            </pre>
          ) : null}
        </>
      )}
    </section>
  );
}
