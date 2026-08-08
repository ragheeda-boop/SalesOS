"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useMemo, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import { useCreateCustomField, useCustomFieldSchema } from "@/lib/hooks/tenantStudioQueries";
import type { StudioFieldType, StudioObjectKey } from "@/lib/api";
import { STUDIO_FIELD_TYPES, STUDIO_OBJECT_KEYS } from "@/lib/api/types/tenantStudio";
import {
  CUSTOM_FIELDS_HONESTY,
  CUSTOM_FIELDS_NON_GOALS,
} from "@/features/tenant-studio/customFieldsHonesty";
import { CustomFieldsAutoRender } from "@/features/tenant-studio/CustomFieldsAutoRender";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-01/02 — Tenant Studio custom field definitions + auto-render preview.
 * Tip STORY-10-01/10-02 HTTP. Not Production GO / RAG GO. TenantList untouched.
 */
export function CustomFieldsStudio() {
  const { toast } = useToast();
  const [objectKey, setObjectKey] = useState<StudioObjectKey>("company");
  const [fieldKey, setFieldKey] = useState("");
  const [fieldType, setFieldType] = useState<StudioFieldType>("string");
  const [label, setLabel] = useState("");
  const [enumCsv, setEnumCsv] = useState("");

  const schemaQuery = useCustomFieldSchema(objectKey);
  const createMutation = useCreateCustomField();

  const enumValues = useMemo(
    () =>
      enumCsv
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    [enumCsv]
  );

  return (
    <div className="space-y-4" data-testid="custom-fields-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="custom-fields-studio-honesty"
      >
        <span className="font-semibold uppercase tracking-wide">Preview</span>
        {" — "}
        {CUSTOM_FIELDS_HONESTY} Non-goals: {CUSTOM_FIELDS_NON_GOALS.join("; ")}. Not Production GO /
        RAG GO.
      </p>

      <div className="flex flex-wrap gap-3">
        <div>
          <label className="block text-xs text-[var(--text-muted)]">Object</label>
          <select
            data-testid="custom-fields-object-select"
            className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={objectKey}
            onChange={(e) => setObjectKey(e.target.value as StudioObjectKey)}
          >
            {STUDIO_OBJECT_KEYS.map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        </div>
        <Button
          data-testid="custom-fields-refresh"
          disabled={schemaQuery.isFetching}
          onClick={() => {
            void schemaQuery.refetch();
          }}
        >
          {schemaQuery.isFetching ? "Refreshing…" : "Refresh schema"}
        </Button>
      </div>

      <div
        className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
        data-testid="custom-fields-schema-meta"
      >
        {schemaQuery.isLoading ? (
          <Spinner className="h-5 w-5" />
        ) : schemaQuery.isError ? (
          <span className="text-[var(--text-danger)]">{getApiError(schemaQuery.error)}</span>
        ) : (
          <>
            schema_version{" "}
            <span className="font-mono">{schemaQuery.data?.schema_version ?? 0}</span>
            {" · "}
            {schemaQuery.data?.fields.length ?? 0} field(s)
          </>
        )}
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="custom-fields-list"
      >
        {(schemaQuery.data?.fields ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No custom fields defined for {objectKey} yet.
          </li>
        ) : (
          (schemaQuery.data?.fields ?? []).map((field) => (
            <li key={field.id} className="px-3 py-2 text-sm" data-testid="custom-fields-row">
              <span className="font-medium">{field.label}</span>{" "}
              <span className="font-mono text-xs">({field.field_key})</span> · {field.field_type}
              {field.enum_values?.length ? ` · enum [${field.enum_values.join(", ")}]` : ""}
              <span className="mt-0.5 block text-xs text-[var(--text-muted)]">
                v{field.schema_version} · {field.id}
              </span>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="custom-fields-create-form"
        onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate(
            {
              object_key: objectKey,
              field_key: fieldKey.trim(),
              field_type: fieldType,
              label: label.trim() || undefined,
              enum_values: fieldType === "enum" ? enumValues : null,
            },
            {
              onSuccess: (row) => {
                toast({
                  variant: "success",
                  title: "Custom field defined",
                  description: `${row.field_key} v${row.schema_version}`,
                });
                setFieldKey("");
                setLabel("");
                setEnumCsv("");
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Define failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Define field (tip POST)
        </h2>
        <Input
          label="field_key"
          data-testid="custom-fields-field-key"
          value={fieldKey}
          onChange={(e) => setFieldKey(e.target.value)}
          placeholder="e.g. renewal_notes"
        />
        <Input
          label="label (optional)"
          data-testid="custom-fields-label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <div>
          <label className="block text-xs text-[var(--text-muted)]">field_type</label>
          <select
            data-testid="custom-fields-field-type"
            className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={fieldType}
            onChange={(e) => setFieldType(e.target.value as StudioFieldType)}
          >
            {STUDIO_FIELD_TYPES.map((ft) => (
              <option key={ft} value={ft}>
                {ft}
              </option>
            ))}
          </select>
        </div>
        {fieldType === "enum" ? (
          <Input
            label="enum_values (comma-separated)"
            data-testid="custom-fields-enum-values"
            value={enumCsv}
            onChange={(e) => setEnumCsv(e.target.value)}
            placeholder="open, won, lost"
          />
        ) : null}
        <Button
          type="submit"
          data-testid="custom-fields-submit"
          disabled={createMutation.isPending || !fieldKey.trim()}
        >
          {createMutation.isPending ? "Defining…" : "Define custom field"}
        </Button>
      </form>

      <div data-testid="custom-fields-auto-preview">
        <h2 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">
          Auto-render preview (tip form-schema)
        </h2>
        <CustomFieldsAutoRender objectKey={objectKey} variant="studio" />
      </div>
    </div>
  );
}
