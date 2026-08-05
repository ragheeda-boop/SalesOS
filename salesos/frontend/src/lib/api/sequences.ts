/**
 * GTM sequencing HTTP (STORY-11-09 / FE-S11-09).
 * Tip email-only in-memory state machine. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/sequences";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface SequenceStepBody {
  id?: string;
  day_offset?: number;
  channel?: string;
  subject: string;
  body?: string;
}

export interface SequenceCreateBody {
  name: string;
  steps: SequenceStepBody[];
  id?: string;
}

export interface SequenceStep {
  id: string;
  day_offset: number;
  channel: string;
  subject: string;
  body: string;
}

export interface SequenceDefinition {
  id: string;
  tenant_id: string;
  name: string;
  steps: SequenceStep[];
  channel: string;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
  step_count: number;
}

export interface EnrollBody {
  contact_email: string;
  linkedin?: string;
  whatsapp?: string;
  id?: string;
}

export interface EnrollmentStepState {
  step_id: string;
  status: string;
  day_offset: number;
}

export interface BoundTaskRef {
  task_id: string;
  title: string;
  source: string;
  completed: boolean;
  step_id: string;
}

export interface BoundActivityRef {
  activity_id: string;
  kind: string;
  summary: string;
  step_id: string;
}

export interface SequenceEnrollment {
  id: string;
  tenant_id: string;
  sequence_id: string;
  contact_email: string;
  contact_handles?: Record<string, string>;
  status: string;
  current_step_index: number;
  step_states: EnrollmentStepState[];
  task_bindings: BoundTaskRef[];
  activity_bindings: BoundActivityRef[];
  last_send?: Record<string, unknown>;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
  bound_to_task_activity: boolean;
}

export interface SequencingMeta {
  object: string;
  /** Tip STORY-11-09 primary channel label (optional after 11-09b). */
  channel?: string;
  /** Tip STORY-11-09b: email + partner LinkedIn/WhatsApp shapes. */
  channels?: string[];
  deferred_channels?: string[];
  linkedin_policy?: string;
  binding: string;
  honesty: string;
}

export async function getSequencingMeta(tenantId: string): Promise<SequencingMeta> {
  const resp = await api.get<SequencingMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listSequences(tenantId: string): Promise<SequenceDefinition[]> {
  const resp = await api.get<SequenceDefinition[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getSequence(
  tenantId: string,
  sequenceId: string
): Promise<SequenceDefinition> {
  const resp = await api.get<SequenceDefinition>(`${BASE}/${sequenceId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function createSequence(
  tenantId: string,
  body: SequenceCreateBody
): Promise<SequenceDefinition> {
  const resp = await api.post<SequenceDefinition>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listEnrollments(tenantId: string): Promise<SequenceEnrollment[]> {
  const resp = await api.get<SequenceEnrollment[]>(`${BASE}/enrollments`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getEnrollment(
  tenantId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  const resp = await api.get<SequenceEnrollment>(`${BASE}/enrollments/${enrollmentId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function enrollContact(
  tenantId: string,
  sequenceId: string,
  body: EnrollBody
): Promise<SequenceEnrollment> {
  const resp = await api.post<SequenceEnrollment>(`${BASE}/${sequenceId}/enrollments`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function advanceEnrollment(
  tenantId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  const resp = await api.post<SequenceEnrollment>(
    `${BASE}/enrollments/${enrollmentId}/advance`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}

export async function pauseEnrollment(
  tenantId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  const resp = await api.post<SequenceEnrollment>(
    `${BASE}/enrollments/${enrollmentId}/pause`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}

export async function resumeEnrollment(
  tenantId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  const resp = await api.post<SequenceEnrollment>(
    `${BASE}/enrollments/${enrollmentId}/resume`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}

export async function cancelEnrollment(
  tenantId: string,
  enrollmentId: string
): Promise<SequenceEnrollment> {
  const resp = await api.post<SequenceEnrollment>(
    `${BASE}/enrollments/${enrollmentId}/cancel`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}
