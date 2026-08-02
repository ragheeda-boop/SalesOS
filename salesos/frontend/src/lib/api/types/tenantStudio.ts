/** Tip STORY-10-01/10-02 Tenant Studio custom field types.
 * Definitions + form-schema / values. In-memory BE — no Postgres claim.
 * Not Production GO / RAG GO.
 */

export type StudioObjectKey = "company" | "contact" | "opportunity";

export type StudioFieldType = "string" | "number" | "date" | "enum";

export const STUDIO_OBJECT_KEYS: StudioObjectKey[] = [
  "company",
  "contact",
  "opportunity",
];

export const STUDIO_FIELD_TYPES: StudioFieldType[] = [
  "string",
  "number",
  "date",
  "enum",
];

export interface CustomFieldCreate {
  object_key: StudioObjectKey;
  field_key: string;
  field_type: StudioFieldType;
  label?: string;
  enum_values?: string[] | null;
}

export interface CustomFieldDefinition {
  id: string;
  tenant_id: string;
  object_key: string;
  field_key: string;
  field_type: string;
  label: string;
  schema_version: number;
  enum_values: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CustomObjectSchema {
  tenant_id: string;
  object_key: string;
  schema_version: number;
  fields: CustomFieldDefinition[];
}

/** Tip STORY-10-02 Form Engine auto-render field descriptor. */
export interface AutoRenderFormField {
  key: string;
  type: string;
  label: string;
  label_ar?: string | null;
  placeholder?: string | null;
  required?: boolean;
  default?: unknown;
  enum?: { label: string; value: string }[] | null;
  order?: number;
  width?: string;
  section?: string | null;
  visible?: boolean;
  disabled?: boolean;
}

/** Tip GET .../form-schema payload. */
export interface CustomFieldsFormSchema {
  id: string;
  title: string;
  description?: string | null;
  fields: AutoRenderFormField[];
  sections?: { id: string; label: string; fields: string[] }[];
  object_key: string;
  tenant_id: string;
  schema_version: number;
  values: Record<string, unknown>;
  bag_key: string;
  renderer: string;
}

export interface CustomFieldValuesRequest {
  values: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface CustomFieldValuesResponse {
  object_key: string;
  bag_key: string;
  values: Record<string, unknown>;
  metadata: Record<string, unknown>;
}
