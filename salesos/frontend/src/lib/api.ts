import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface Company {
  id: string;
  name_ar: string;
  name_en: string | null;
  cr_number: string;
  status: string;
  city: string | null;
  region: string | null;
  phone: string | null;
  email: string | null;
  confidence_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface CompanySearchParams {
  q?: string;
  cr_number?: string;
  status?: string;
  city?: string;
  page?: number;
  page_size?: number;
}

export interface Branch {
  id: string;
  name: string;
  city: string | null;
  region: string | null;
  phone: string | null;
}

export interface License {
  id: string;
  license_type: string;
  license_number: string;
  status: string;
  issue_date: string | null;
  expiry_date: string | null;
}

export interface Contact {
  id: string;
  name: string;
  name_ar?: string | null;
  email: string | null;
  phone: string | null;
  mobile?: string | null;
  position: string | null;
  position_ar?: string | null;
  department?: string | null;
  company_id?: string | null;
  company_name?: string;
  is_primary?: boolean;
  source?: string | null;
  confidence_score?: number | null;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ContactCreateRequest {
  name: string;
  name_ar?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  position?: string;
  position_ar?: string;
  department?: string;
  company_id?: string;
  is_primary?: boolean;
  source?: string;
  tags?: string[];
}

export interface ContactUpdateRequest {
  name?: string;
  name_ar?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  position?: string;
  position_ar?: string;
  department?: string;
  is_primary?: boolean;
  tags?: string[];
}

export interface ContactSearchParams {
  q?: string;
  company_id?: string;
  email?: string;
  source?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export async function searchContacts(
  params: ContactSearchParams,
  tenantId: string
): Promise<PaginatedResponse<Contact>> {
  const response = await api.get("/api/v1/contacts", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getContact(id: string, tenantId: string): Promise<Contact> {
  const response = await api.get(`/api/v1/contacts/${id}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function createContact(
  data: ContactCreateRequest,
  tenantId: string
): Promise<Contact> {
  const response = await api.post("/api/v1/contacts", data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function updateContact(
  id: string,
  data: ContactUpdateRequest,
  tenantId: string
): Promise<Contact> {
  const response = await api.patch(`/api/v1/contacts/${id}`, data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function deleteContact(id: string, tenantId: string): Promise<void> {
  await api.delete(`/api/v1/contacts/${id}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
}

export async function getContactsByCompany(
  companyId: string,
  tenantId: string
): Promise<Contact[]> {
  const response = await api.get(`/api/v1/contacts/by-company/${companyId}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export interface CompanyDetail extends Company {
  branches: Branch[];
  licenses: License[];
  contacts: Contact[];
}

export async function createCompany(
  data: {
    name_ar: string;
    cr_number: string;
    name_en?: string;
    status?: string;
    city?: string;
    region?: string;
  },
  tenantId: string
): Promise<Company> {
  const response = await api.post("/api/v1/companies", data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function updateCompany(
  id: string,
  data: Record<string, unknown>,
  tenantId: string
): Promise<Company> {
  const response = await api.patch(`/api/v1/companies/${id}`, data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function deleteCompany(id: string, tenantId: string): Promise<void> {
  await api.delete(`/api/v1/companies/${id}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
}

export async function addCompanyContact(
  companyId: string,
  data: { name: string; position?: string; email?: string; phone?: string },
  tenantId: string
): Promise<Contact> {
  const response = await api.post(`/api/v1/companies/${companyId}/contacts`, data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function searchCompanies(
  params: CompanySearchParams,
  tenantId: string
): Promise<PaginatedResponse<Company>> {
  const response = await api.get("/api/v1/companies", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getCompany(id: string, tenantId: string): Promise<CompanyDetail> {
  const response = await api.get(`/api/v1/companies/${id}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Company 360 ──────────────────────────────────────────────
export interface Company360Overview {
  total_contacts: number;
  total_opportunities: number;
  total_revenue: number;
  active_contracts: number;
  pending_tasks: number;
  upcoming_meetings: number;
  last_activity: string | null;
  signal_count: number;
  contacts_page: number;
  contacts_total: number;
  opportunities_page: number;
  opportunities_total: number;
  timeline_page: number;
  timeline_total: number;
}

export interface Company360Organization {
  branches: Branch[];
  departments: string[];
  employees_count: number;
  legal_form: string | null;
  incorporation_date: string | null;
}

export interface Company360Signals {
  items: Record<string, unknown>[];
  total: number;
}

export interface Company360Response {
  company: CompanyDetail;
  overview: Company360Overview;
  organization: Company360Organization;
  enrichment?: { sources: string[]; is_golden_record: boolean; confidence_score: number; last_enriched_at: string | null };
  golden_record_id?: string | null;
  golden_record_data?: Record<string, any> | null;
  related_entities?: any[];
  decision_makers?: any[];
  contacts: Record<string, unknown>[];
  assigned_employees: Record<string, unknown>[];
  opportunities: Record<string, unknown>[];
  contracts: Record<string, unknown>[];
  invoices: Record<string, unknown>[];
  timeline: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  emails: Record<string, unknown>[];
  meetings: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  signals: Company360Signals;
  branches: Branch[];
  licenses: License[];
}

export async function getCompany360(id: string, tenantId: string): Promise<Company360Response> {
  const response = await api.get(`/api/v1/companies/${id}/360`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Employee 360 ─────────────────────────────────────────────
export interface EmployeeProfile {
  id: string;
  full_name: string;
  full_name_ar: string | null;
  email: string;
  role: string;
  phone: string | null;
  avatar_url: string | null;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  team: Record<string, unknown>[];
  manager: Record<string, unknown> | null;
}

export interface EmployeePortfolio {
  companies: Record<string, unknown>[];
  contacts: Record<string, unknown>[];
  pipeline: { id: string; name: string; type: string; value: number; status: string; company_id?: string; company_name?: string }[];
  revenue: number;
  contracts: { id: string; name: string; type: string; value: number; status: string }[];
  projects: Record<string, unknown>[];
}

export interface ActivityIntelligence {
  meetings: number;
  emails: number;
  calls: number;
  tasks: number;
  notes: number;
  documents: number;
  total: number;
  recent: Record<string, unknown>[];
}

export interface CalendarIntelligence {
  today_count: number;
  week_count: number;
  month_count: number;
  total_hours: number;
  avg_duration_minutes: number;
  unique_companies_met: number;
  upcoming: Record<string, unknown>[];
}

export interface EmailIntelligence {
  sent: number;
  received: number;
  replies: number;
  avg_response_hours: number;
  top_contacts: Record<string, unknown>[];
  top_companies: Record<string, unknown>[];
}

export interface EmployeeKPIs {
  revenue: number;
  pipeline: number;
  win_rate: number;
  response_rate: number;
  follow_up_rate: number;
  activities: number;
  productivity: number;
  forecast: number;
}

export interface AICoachAction {
  type: string;
  title: string;
  description: string;
  priority: string;
  target_id?: string;
  target_type?: string;
}

export interface Employee360Response {
  profile: EmployeeProfile;
  portfolio: EmployeePortfolio;
  calendar_intelligence: CalendarIntelligence;
  email_intelligence: EmailIntelligence;
  activity_intelligence: ActivityIntelligence;
  kpis: EmployeeKPIs;
  ai_coach: AICoachAction[];
}

export async function getEmployee360(id: string, tenantId: string): Promise<Employee360Response> {
  const response = await api.get(`/api/v1/employees/${id}/360`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getMy360(tenantId: string): Promise<Employee360Response> {
  const response = await api.get("/api/v1/employees/me/360", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Executive Dashboard ─────────────────────────────────────
export interface RevenueKPI {
  total_booked: number;
  total_pipeline: number;
  weighted_pipeline: number;
  forecast: number;
  growth_percent: number;
}

export interface TeamKPI {
  total_employees: number;
  active_employees: number;
  top_performers: Record<string, unknown>[];
  avg_win_rate: number;
}

export interface RiskKPI {
  expiring_contracts: number;
  stalled_deals: number;
  inactive_companies: number;
  low_pipeline_employees: number;
}

export interface PipelineHealth {
  total_deals: number;
  total_value: number;
  won_deals: number;
  lost_deals: number;
  win_rate: number;
  avg_deal_size: number;
  by_stage: { stage: string; cnt: number; val: number }[];
}

export interface RenewalKPI {
  due_next_30_days: number;
  due_next_90_days: number;
  total_renewal_value: number;
  at_risk: Record<string, unknown>[];
}

export interface GrowthKPI {
  new_companies_30d: number;
  new_contacts_30d: number;
  new_opportunities_30d: number;
  new_contracts_30d: number;
}

export interface HealthKPI {
  overall_health: string;
  data_completeness: number;
  sync_status: string;
  last_activity: string;
}

export interface ExecutiveDashboardResponse {
  revenue: RevenueKPI;
  team: TeamKPI;
  risk: RiskKPI;
  health: HealthKPI;
  pipeline: PipelineHealth;
  renewals: RenewalKPI;
  growth: GrowthKPI;
}

export async function getExecutiveDashboard(tenantId: string): Promise<ExecutiveDashboardResponse> {
  const response = await api.get("/api/v1/executive/dashboard", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Opportunities / Pipeline ────────────────────────────────
export interface Opportunity {
  id: string;
  name: string;
  stage: string;
  value: number;
  company_id: string;
  company_name?: string;
  probability?: number;
  expected_close_date?: string;
  owner_id?: string;
  status?: string;
  won_amount?: number;
  loss_reason?: string;
}

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
}

export async function listOpportunities(tenantId: string): Promise<OpportunityListResponse> {
  const response = await api.get("/api/v1/opportunities", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function createOpportunity(
  tenantId: string,
  companyId: string,
  name: string,
  value = 0
) {
  const response = await api.post("/api/v1/opportunities", null, {
    params: { company_id: companyId, name, value },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function advanceOpportunity(opportunityId: string, toStage: string) {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/advance`, null, {
    params: { to_stage: toStage },
  });
  return response.data;
}

export async function closeWon(opportunityId: string, amount?: number) {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/won`, null, {
    params: amount ? { amount } : undefined,
  });
  return response.data;
}

export async function closeLost(opportunityId: string, reason = "") {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/lost`, null, {
    params: reason ? { reason } : undefined,
  });
  return response.data;
}

export interface Pipeline {
  id: string;
  name: string;
  stages: number;
}

export interface PipelineListResponse {
  items: Pipeline[];
}

export async function listPipelines(tenantId: string): Promise<PipelineListResponse> {
  const response = await api.get("/api/v1/pipelines", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Activity / Timeline ─────────────────────────────────────
export interface ActivityRecord {
  id: string;
  tenant_id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  target_type?: string;
  target_id?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface EntityActivityResponse {
  entity_type: string;
  entity_id: string;
  items: ActivityRecord[];
  total: number;
}

export interface ActivityQueryResponse {
  items: ActivityRecord[];
  total: number;
  limit: number;
  offset: number;
}

export async function getEntityActivities(
  entityType: string,
  entityId: string,
  tenantId: string,
  limit = 50,
  offset = 0
): Promise<EntityActivityResponse> {
  const response = await api.get(`/api/v1/activities/${entityType}/${entityId}`, {
    params: { limit, offset },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function queryActivities(
  params: Record<string, string | number | undefined>,
  tenantId: string
): Promise<ActivityQueryResponse> {
  const response = await api.get("/api/v1/activities", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Unified Search ───────────────────────────────────────────
export interface SearchResultItem {
  id: string;
  type: string;
  score: number;
  data: Record<string, unknown>;
  matched_fields?: string[];
  explanation?: string;
}

export interface SearchResponse {
  query: string;
  strategy: string;
  total: number;
  took_ms: number;
  items: SearchResultItem[];
  facets?: Record<string, Record<string, number>>;
  suggestions?: string[];
}

export interface SearchParams {
  q: string;
  strategy?: "fulltext" | "semantic" | "graph" | "hybrid";
  limit?: number;
  offset?: number;
  include_facets?: boolean;
  city?: string;
  region?: string;
  industry?: string;
  status?: string;
}

export async function unifiedSearch(
  params: SearchParams,
  tenantId: string
): Promise<SearchResponse> {
  const response = await api.get("/api/v1/search", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function login(email: string, password: string) {
  const response = await api.post("/api/v1/identity/login", { email, password });
  const { access_token, refresh_token } = response.data;
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
  return response.data;
}

export async function register(
  email: string,
  password: string,
  fullName: string
) {
  const response = await api.post("/api/v1/identity/register", {
    email,
    password,
    full_name: fullName,
  });
  const { access_token, refresh_token } = response.data;
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
  return response.data;
}

// ─── Admin / Monitoring ──────────────────────────────────────
export interface PipelineMetrics {
  records_ingested: number;
  total_valid: number;
  total_errors: number;
  errors_by_stage: Record<string, number>;
  golden_records_created: number;
  golden_records_merged: number;
  companies_synced: number;
  embeddings_stored: number;
  kg_triples_created: number;
  features_computed: number;
  stage_durations_ms: Record<string, number>;
  total_duration_ms: number;
  last_run_at: string | null;
}

export interface FeatureStoreMetrics {
  computations: number;
  errors: number;
  cache_hits: number;
  cache_misses: number;
  total_compute_ms: number;
}

export interface FullHealthResponse {
  status: string;
  checks: Record<string, string>;
  pipeline: PipelineMetrics | { status: string };
}

export interface GoldenRecordAdmin {
  id: string;
  tenant_id: string;
  cr_number: string | null;
  company_name_ar: string | null;
  status: string;
  confidence_score: number | null;
  source_records: number;
  created_at: string;
  updated_at: string;
}

export interface EntityResolutionConflict {
  id: string;
  tenant_id: string;
  cr_number_a: string;
  cr_number_b: string;
  status: string;
  reason: string;
  created_at: string;
}

export async function getAdminHealth(
  tenantId: string
): Promise<FullHealthResponse> {
  const response = await api.get("/api/v1/admin/health/full", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getAdminMetrics(
  tenantId: string
): Promise<string> {
  const response = await api.get("/api/v1/admin/metrics", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listGoldenRecords(
  tenantId: string,
  params: { page?: number; page_size?: number; status?: string } = {}
): Promise<PaginatedResponse<GoldenRecordAdmin>> {
  const response = await api.get("/api/v1/entity-resolution/golden-records", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listConflicts(
  tenantId: string,
  params: { page?: number; page_size?: number; status?: string } = {}
): Promise<PaginatedResponse<EntityResolutionConflict>> {
  const response = await api.get("/api/v1/entity-resolution/conflicts", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

// ─── Dead Letter Queue ──────────────────────────────────────
export interface DlqEntry {
  id: number;
  source_slug: string;
  cr_number: string | null;
  stage: string;
  error_message: string;
  error_type: string | null;
  retry_count: number;
  max_retries: number;
  status: string;
  created_at: string;
  last_retry_at: string | null;
}

export interface DlqRetryResponse {
  processed: number;
  retried: number;
  resolved: number;
  still_failed: number;
}

export async function listDlq(
  tenantId: string,
  params: { page?: number; page_size?: number; status?: string; stage?: string } = {}
): Promise<PaginatedResponse<DlqEntry>> {
  const response = await api.get("/api/v1/admin/dlq", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function retryDlq(
  tenantId: string,
  limit = 50
): Promise<DlqRetryResponse> {
  const response = await api.post("/api/v1/admin/dlq/retry", null, {
    params: { limit },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function purgeDlq(
  tenantId: string,
  status?: string
): Promise<{ purged: number }> {
  const response = await api.delete("/api/v1/admin/dlq", {
    params: status ? { status } : undefined,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getDlqStats(
  tenantId: string
): Promise<{ failed_by_stage: Record<string, number> }> {
  const response = await api.get("/api/v1/admin/dlq/stats", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
