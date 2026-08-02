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

/** Tip STORY-10-04 Scoring Rules Studio (deterministic, in-memory). */
export type ScoringTargetType = "lead" | "company" | "opportunity";

export type ScoringBoostOp =
  "eq" | "neq" | "gte" | "lte" | "gt" | "lt" | "contains" | "exists";

export const SCORING_TARGET_TYPES: ScoringTargetType[] = [
  "lead",
  "company",
  "opportunity",
];

export const SCORING_BOOST_OPS: ScoringBoostOp[] = [
  "eq",
  "neq",
  "gte",
  "lte",
  "gt",
  "lt",
  "contains",
  "exists",
];

/** Mirror tip PLATFORM_DEFAULT_WEIGHTS — form defaults only. */
export const PLATFORM_DEFAULT_DIMENSION_WEIGHTS: Record<string, number> = {
  buying_intent: 0.3,
  engagement: 0.2,
  fit: 0.15,
  urgency: 0.15,
  relationship: 0.1,
  market_signal: 0.1,
};

export const SCORING_DIMENSIONS = Object.keys(
  PLATFORM_DEFAULT_DIMENSION_WEIGHTS,
);

export interface ScoringBoost {
  field: string;
  op: ScoringBoostOp;
  value?: unknown;
  delta: number;
}

export interface ScoringRuleUpsert {
  id?: string | null;
  name: string;
  target_type: ScoringTargetType;
  dimension_weights: Record<string, number>;
  boosts?: ScoringBoost[];
  active?: boolean;
}

export interface ScoringRule {
  id: string;
  tenant_id: string;
  name: string;
  target_type: string;
  dimension_weights: Record<string, number>;
  boosts: ScoringBoost[];
  active: boolean;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

export interface ScoringEvaluateRequest {
  target_type: ScoringTargetType;
  dimension_scores: Record<string, number>;
  attributes?: Record<string, unknown>;
  rule_id?: string | null;
}

export interface ScoringEvaluateResponse {
  score: number;
  source: string;
  fallback_used: boolean;
  fallback_reason?: string | null;
  rule_id?: string | null;
  explanation: string[];
  dimension_weights_used: Record<string, number>;
}

/** Tip STORY-10-06 Permissions Studio (custom roles + entitlement ceiling). */
export type StudioPlanTier = "starter" | "growth" | "enterprise";

export const STUDIO_PLAN_TIERS: StudioPlanTier[] = [
  "starter",
  "growth",
  "enterprise",
];

export interface StudioPermissionCatalogItem {
  key: string;
  name: string;
  description: string;
  domain: string;
  group: string;
  requires_publish: boolean;
  within_ceiling: boolean;
  ceiling_reason?: string | null;
}

export interface PermissionsCeilingSummary {
  enabled_domains: string[];
  publish_domains: string[];
  grantable_permissions: string[];
  entitlements?: Record<string, unknown>;
  version?: number;
}

export interface SetPermissionsCeilingBody {
  plan_tier?: string | null;
  entitlements?: Record<string, unknown> | null;
}

export interface CeilingCheckRequest {
  permissions: string[];
  plan_tier?: string | null;
  entitlements?: Record<string, unknown> | null;
}

export interface CeilingCheckResponse {
  allowed: boolean;
  rejected: string[];
  reasons: Record<string, string>;
  grantable: string[];
}

export interface CustomRoleUpsert {
  id?: string | null;
  name: string;
  description?: string;
  permissions: string[];
  plan_tier?: string | null;
  entitlements?: Record<string, unknown> | null;
}

export interface CustomRole {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  permissions: string[];
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

/** Tip STORY-10-03 Workflow Builder canvas (no for_each). */
export type WorkflowCanvasNodeKind = "action" | "branch";

/** Action step types allowed on tip canvas (for_each / parallel deferred). */
export const WORKFLOW_ACTION_STEP_TYPES = [
  "send_email",
  "update_crm",
  "create_task",
  "webhook",
  "nba_recommend",
  "set_variable",
  "log_message",
] as const;

export type WorkflowActionStepType =
  (typeof WORKFLOW_ACTION_STEP_TYPES)[number];

export interface WorkflowCanvasNode {
  id: string;
  kind: WorkflowCanvasNodeKind;
  step_type?: string;
  config?: Record<string, unknown>;
  condition?: string | null;
  then_nodes?: WorkflowCanvasNode[];
  else_nodes?: WorkflowCanvasNode[];
}

export interface WorkflowCanvasUpsert {
  id?: string | null;
  name: string;
  description?: string;
  trigger_type?: string;
  nodes?: WorkflowCanvasNode[];
}

export interface WorkflowCanvas {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  trigger_type: string;
  nodes: WorkflowCanvasNode[];
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowCanvasCompileResult {
  canvas_id?: string;
  schema_version?: number;
  workflow: Record<string, unknown>;
}
