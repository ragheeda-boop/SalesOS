/** Tip STORY-10-01 Tenant Studio custom field definition types.
 * Definition HTTP only — no value persistence / auto-render (STORY-10-02).
 * In-memory BE store on tip. Not Production GO / RAG GO.
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
