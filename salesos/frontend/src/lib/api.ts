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
  position: string | null;
  phone: string | null;
  email: string | null;
}

export interface CompanyDetail extends Company {
  branches: Branch[];
  licenses: License[];
  contacts: Contact[];
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
