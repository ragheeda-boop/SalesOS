import api from"./client";
import type { Branch, Company, CompanyDetail, CompanySearchParams, Contact, ContactCreateRequest, ContactSearchParams, ContactUpdateRequest, CursorResponse, License, PaginatedResponse, Company360Response } from"./types";

export async function searchContacts(
 params: ContactSearchParams,
 tenantId: string
): Promise<PaginatedResponse<Contact>> {
 const response = await api.get("/api/v1/contacts", {
 params,
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function getContact(id: string, tenantId: string): Promise<Contact> {
 const response = await api.get(`/api/v1/contacts/${id}`, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function createContact(
 data: ContactCreateRequest,
 tenantId: string
): Promise<Contact> {
 const response = await api.post("/api/v1/contacts", data, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function updateContact(
 id: string,
 data: ContactUpdateRequest,
 tenantId: string
): Promise<Contact> {
 const response = await api.patch(`/api/v1/contacts/${id}`, data, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function deleteContact(id: string, tenantId: string): Promise<void> {
 await api.delete(`/api/v1/contacts/${id}`, {
 headers: {"X-Tenant-Id": tenantId },
 });
}

export async function getContactsByCompany(
 companyId: string,
 tenantId: string
): Promise<Contact[]> {
 const response = await api.get(`/api/v1/contacts/by-company/${companyId}`, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
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
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function updateCompany(
 id: string,
 data: Record<string, unknown>,
 tenantId: string
): Promise<Company> {
 const response = await api.patch(`/api/v1/companies/${id}`, data, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function deleteCompany(id: string, tenantId: string): Promise<void> {
 await api.delete(`/api/v1/companies/${id}`, {
 headers: {"X-Tenant-Id": tenantId },
 });
}

export async function addCompanyContact(
 companyId: string,
 data: { name: string; position?: string; email?: string; phone?: string },
 tenantId: string
): Promise<Contact> {
 const response = await api.post(`/api/v1/companies/${companyId}/contacts`, data, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function searchCompanies(
 params: CompanySearchParams,
 tenantId: string
): Promise<PaginatedResponse<Company>> {
 const response = await api.get("/api/v1/companies", {
 params: { ...params, cursor: undefined },
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function searchCompaniesCursor(
 params: CompanySearchParams,
 tenantId: string
): Promise<CursorResponse<Company>> {
 const response = await api.get("/api/v1/companies/cursors", {
 params,
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function getCompany(id: string, tenantId: string): Promise<CompanyDetail> {
 const response = await api.get(`/api/v1/companies/${id}`, {
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function getCompany360(id: string, tenantId: string): Promise<Company360Response> {
 const response = await api.get(`/api/v1/companies/${id}/360`, {
  headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function getCompanyIntelligence(id: string, tenantId: string) {
 const response = await api.get(`/api/v1/companies/${id}/intelligence`, {
  headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}
