import type { CursorResponse, PaginatedResponse } from"./common";

export { CursorResponse, PaginatedResponse };

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
 cursor?: string;
 sort_by?: string;
 sort_order?: string;
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

export interface CompanyDetail extends Company {
 branches: Branch[];
 licenses: License[];
 contacts: Contact[];
}

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
 golden_record_data?: Record<string, unknown> | null;
 related_entities?: { id: string; name: string; type: string; confidence: number }[];
 decision_makers?: { id: string; name: string; role: string; department: string; influence: string; connected: boolean; email?: string; lastInteraction?: string }[];
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
 health_score?: number;
}
