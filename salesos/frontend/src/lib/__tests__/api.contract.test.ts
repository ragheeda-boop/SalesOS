const mockAxios = {
  create: jest.fn(() => mockAxios),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
};
jest.mock("axios", () => mockAxios);
import {
  searchCompanies,
  searchCompaniesCursor,
  getCompany,
  createCompany,
  updateCompany,
  deleteCompany,
  searchContacts,
  getContact,
  createContact,
  updateContact,
  deleteContact,
  getContactsByCompany,
  searchEmployees,
  getEmployee360,
  getEmployeeScore,
  getEmployeeTimeline,
  bulkEditEmployees,
  bulkDeleteEmployees,
  exportEmployees,
  unifiedSearch,
  getExecutiveDashboard,
  listOpportunities,
  createOpportunity,
  listPipelines,
  getEntityActivities,
  login,
  register,
  getCurrentUser,
  changePassword,
  getCompany360,
  listDlq,
  retryDlq,
  purgeDlq,
  listGoldenRecords,
  listConflicts,
  listTasks,
  completeTask,
  submitCopilotFeedback,
  getCopilotTelemetry,
  listAdminTenants,
  listAdminPlans,
  listAdminUsers,
  getAdminDetailedHealth,
  getAdminAICostSummary,
  listAdminAuditLogs,
  getMy360,
  getEmployeeSignals,
  getEmployeePerformance,
  addCompanyContact,
  advanceOpportunity,
  closeWon,
  closeLost,
  getGlobalActivities,
  queryActivities,
  createTask,
  getDlqStats,
  getAdminTenant,
  createAdminTenant,
  updateAdminTenant,
  deleteAdminTenant,
  getAdminTenantUsage,
  listAdminLicenses,
  createAdminLicense,
  getAdminUser,
  listAdminInvoices,
  listAdminTransactions,
  createAdminFeatureFlag,
  updateAdminFeatureFlag,
  getAdminFlagTenants,
  toggleAdminFlagForTenant,
  listAdminJobs,
  getAdminJob,
  retryAdminJob,
  listAdminAICosts,
  getAdminAIUsage,
  getAdminHealthHistory,
  listAdminPermissions,
  listAdminRoles,
  createAdminRole,
  updateAdminRole,
  deleteAdminRole,
  getAdminConfig,
  saveAdminConfig,
  validateAdminConfig,
} from "../api";

function mockResponse(data: unknown) {
  return { data };
}

const TENANT = "tenant-123";

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});

// ─── Company API Contracts ────────────────────────────────────

describe("searchCompanies — contract", () => {
  it("returns PaginatedResponse<Company>", async () => {
    const payload = {
      total: 42,
      page: 1,
      page_size: 10,
      items: [
        {
          id: "c-1",
          name_ar: "أرامكو",
          name_en: "Aramco",
          cr_number: "1010000001",
          status: "نشط",
          city: "الظهران",
          region: null,
          phone: null,
          email: null,
          confidence_score: 0.9,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-07-10T00:00:00Z",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await searchCompanies({ q: "أرامكو" }, TENANT);

    expect(result.total).toBe(42);
    expect(result.page).toBe(1);
    expect(result.page_size).toBe(10);
    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("id");
    expect(result.items[0]).toHaveProperty("name_ar");
    expect(result.items[0]).toHaveProperty("cr_number");
    expect(mockAxios.get).toHaveBeenCalledWith(
      "/api/v1/companies",
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });

  it("strips cursor from params for offset pagination", async () => {
    mockAxios.get.mockResolvedValueOnce(
      mockResponse({ total: 0, page: 1, page_size: 10, items: [] }),
    );

    await searchCompanies({ q: "test", cursor: "abc" }, TENANT);

    const callParams = mockAxios.get.mock.calls[0][1].params;
    expect(callParams.cursor).toBeUndefined();
  });

  it("normalizes CursorResponse data into PaginatedResponse items", async () => {
    const payload = {
      data: [
        {
          id: "c-1",
          name_ar: "أرامكو",
          name_en: "Aramco",
          cr_number: "101",
          status: "نشط",
          city: null,
          region: null,
          phone: null,
          email: null,
          confidence_score: null,
          created_at: "2026-01-01",
          updated_at: "2026-07-10",
        },
      ],
      next_cursor: null,
      has_next: false,
      total: 141221,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await searchCompanies({ page: 1, page_size: 50 }, TENANT);

    expect(result.total).toBe(141221);
    expect(result.items).toHaveLength(1);
    expect(result.items[0].id).toBe("c-1");
    expect(result.page).toBe(1);
    expect(result.page_size).toBe(50);
  });
});

describe("searchCompaniesCursor — contract", () => {
  it("returns CursorResponse<Company>", async () => {
    const payload = {
      data: [
        {
          id: "c-1",
          name_ar: "أرامكو",
          name_en: "Aramco",
          cr_number: "101",
          status: "نشط",
          city: null,
          region: null,
          phone: null,
          email: null,
          confidence_score: null,
          created_at: "2026-01-01",
          updated_at: "2026-07-10",
        },
      ],
      next_cursor: "cursor-abc",
      previous_cursor: null,
      has_next: true,
      has_previous: false,
      total: 50,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await searchCompaniesCursor({ page_size: 10 }, TENANT);

    expect(Array.isArray(result.data)).toBe(true);
    expect(typeof result.has_next).toBe("boolean");
    expect(result.next_cursor).toBeDefined();
    expect(mockAxios.get).toHaveBeenCalledWith(
      "/api/v1/companies/cursors",
      expect.anything(),
    );
  });
});

describe("getCompany — contract", () => {
  it("returns CompanyDetail with branches, licenses, contacts", async () => {
    const payload = {
      id: "c-1",
      name_ar: "أرامكو",
      name_en: "Aramco",
      cr_number: "101",
      status: "نشط",
      city: "الظهران",
      region: null,
      phone: null,
      email: null,
      confidence_score: 0.9,
      created_at: "2026-01-01",
      updated_at: "2026-07-10",
      branches: [
        {
          id: "b-1",
          name: "فرع الرياض",
          city: "الرياض",
          region: null,
          phone: null,
        },
      ],
      licenses: [
        {
          id: "l-1",
          license_type: "تجارية",
          license_number: "L001",
          status: "نشط",
          issue_date: null,
          expiry_date: null,
        },
      ],
      contacts: [
        {
          id: "ct-1",
          name: "أحمد",
          email: null,
          phone: null,
          position: "مدير",
          company_id: "c-1",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getCompany("c-1", TENANT);

    expect(result.id).toBe("c-1");
    expect(Array.isArray(result.branches)).toBe(true);
    expect(Array.isArray(result.licenses)).toBe(true);
    expect(Array.isArray(result.contacts)).toBe(true);
  });
});

describe("createCompany — contract", () => {
  it("returns created Company", async () => {
    const payload = {
      id: "c-new",
      name_ar: "شركة جديدة",
      cr_number: "999",
      status: "نشط",
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
      name_en: null,
      city: null,
      region: null,
      phone: null,
      email: null,
      confidence_score: null,
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createCompany(
      { name_ar: "شركة جديدة", cr_number: "999" },
      TENANT,
    );

    expect(result.id).toBe("c-new");
    expect(result.name_ar).toBe("شركة جديدة");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/companies",
      expect.anything(),
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

describe("updateCompany — contract", () => {
  it("returns updated Company", async () => {
    const payload = {
      id: "c-1",
      name_ar: "أرامكو المحدّثة",
      cr_number: "101",
      status: "نشط",
      created_at: "2026-01-01",
      updated_at: "2026-07-16",
      name_en: null,
      city: null,
      region: null,
      phone: null,
      email: null,
      confidence_score: null,
    };
    mockAxios.patch.mockResolvedValueOnce(mockResponse(payload));

    const result = await updateCompany(
      "c-1",
      { name_ar: "أرامكو المحدّثة" },
      TENANT,
    );

    expect(result.name_ar).toBe("أرامكو المحدّثة");
    expect(mockAxios.patch).toHaveBeenCalledWith(
      "/api/v1/companies/c-1",
      expect.anything(),
      expect.anything(),
    );
  });
});

describe("deleteCompany — contract", () => {
  it("sends DELETE and returns void", async () => {
    mockAxios.delete.mockResolvedValueOnce(mockResponse(undefined));

    await deleteCompany("c-1", TENANT);

    expect(mockAxios.delete).toHaveBeenCalledWith(
      "/api/v1/companies/c-1",
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

// ─── Contact API Contracts ────────────────────────────────────

describe("searchContacts — contract", () => {
  it("returns PaginatedResponse<Contact>", async () => {
    const payload = {
      total: 5,
      page: 1,
      page_size: 10,
      items: [
        {
          id: "ct-1",
          name: "أحمد",
          name_ar: null,
          email: "a@test.com",
          phone: null,
          mobile: null,
          position: "مدير",
          position_ar: null,
          department: null,
          company_id: "c-1",
          company_name: null,
          is_primary: false,
          source: null,
          confidence_score: null,
          tags: [],
          created_at: "2026-01-01",
          updated_at: "2026-07-10",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await searchContacts({ q: "أحمد" }, TENANT);

    expect(result.total).toBe(5);
    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("id");
    expect(result.items[0]).toHaveProperty("name");
    expect(result.items[0]).toHaveProperty("position");
  });
});

describe("getContact — contract", () => {
  it("returns single Contact", async () => {
    const payload = {
      id: "ct-1",
      name: "أحمد",
      email: "a@test.com",
      phone: null,
      position: "مدير",
      company_id: "c-1",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getContact("ct-1", TENANT);

    expect(result.id).toBe("ct-1");
    expect(result.name).toBe("أحمد");
  });
});

describe("createContact — contract", () => {
  it("returns created Contact", async () => {
    const payload = {
      id: "ct-new",
      name: "نورة",
      email: "n@test.com",
      phone: null,
      position: "مديرة",
      company_id: "c-1",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createContact(
      { name: "نورة", email: "n@test.com" },
      TENANT,
    );

    expect(result.id).toBe("ct-new");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/contacts",
      expect.anything(),
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

describe("updateContact — contract", () => {
  it("returns updated Contact via PATCH", async () => {
    const payload = { id: "ct-1", name: "أحمد المحدّث", position: " CFO" };
    mockAxios.patch.mockResolvedValueOnce(mockResponse(payload));

    const result = await updateContact(
      "ct-1",
      { name: "أحمد المحدّث" },
      TENANT,
    );

    expect(result.name).toBe("أحمد المحدّث");
    expect(mockAxios.patch).toHaveBeenCalledWith(
      "/api/v1/contacts/ct-1",
      expect.anything(),
      expect.anything(),
    );
  });
});

describe("deleteContact — contract", () => {
  it("sends DELETE", async () => {
    mockAxios.delete.mockResolvedValueOnce(mockResponse(undefined));

    await deleteContact("ct-1", TENANT);

    expect(mockAxios.delete).toHaveBeenCalledWith(
      "/api/v1/contacts/ct-1",
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

describe("getContactsByCompany — contract", () => {
  it("returns Contact[]", async () => {
    const payload = [
      {
        id: "ct-1",
        name: "أحمد",
        email: null,
        phone: null,
        position: "مدير",
        company_id: "c-1",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getContactsByCompany("c-1", TENANT);

    expect(Array.isArray(result)).toBe(true);
    expect(result[0].company_id).toBe("c-1");
  });
});

// ─── Employee API Contracts ───────────────────────────────────

describe("searchEmployees — contract", () => {
  it("returns CursorResponse<EmployeeListItem>", async () => {
    const payload = {
      data: [
        {
          id: "e-1",
          full_name: "خالد",
          full_name_ar: null,
          email: "k@test.com",
          role: "admin",
          department: null,
          phone: null,
          avatar_url: null,
          is_active: true,
          signal_count: 5,
          score: 82,
          score_trend: "up",
          confidence: 0.9,
          created_at: "2026-01-01",
        },
      ],
      next_cursor: null,
      previous_cursor: null,
      has_next: false,
      has_previous: false,
      total: 1,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await searchEmployees({ q: "خالد" }, TENANT);

    expect(Array.isArray(result.data)).toBe(true);
    expect(typeof result.has_next).toBe("boolean");
    expect(result.data[0]).toHaveProperty("full_name");
    expect(result.data[0]).toHaveProperty("score");
  });
});

describe("getEmployee360 — contract", () => {
  it("returns Employee360Response with all sections", async () => {
    const payload = {
      profile: {
        id: "e-1",
        full_name: "خالد",
        full_name_ar: null,
        email: "k@test.com",
        role: "admin",
        phone: null,
        avatar_url: null,
        is_active: true,
        tenant_id: TENANT,
        created_at: "2026-01-01",
        team: [],
        manager: null,
      },
      portfolio: {
        companies: [],
        contacts: [],
        pipeline: [],
        revenue: 0,
        contracts: [],
        projects: [],
      },
      calendar_intelligence: {
        today_count: 0,
        week_count: 0,
        month_count: 0,
        total_hours: 0,
        avg_duration_minutes: 0,
        unique_companies_met: 0,
        upcoming: [],
      },
      email_intelligence: {
        sent: 0,
        received: 0,
        replies: 0,
        avg_response_hours: 0,
        top_contacts: [],
        top_companies: [],
      },
      activity_intelligence: {
        meetings: 0,
        emails: 0,
        calls: 0,
        tasks: 0,
        notes: 0,
        documents: 0,
        total: 0,
        recent: [],
      },
      kpis: {
        revenue: 0,
        pipeline: 0,
        win_rate: 0,
        response_rate: 0,
        follow_up_rate: 0,
        activities: 0,
        productivity: 0,
        forecast: 0,
      },
      ai_coach: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEmployee360("e-1", TENANT);

    expect(result).toHaveProperty("profile");
    expect(result).toHaveProperty("portfolio");
    expect(result).toHaveProperty("kpis");
    expect(result).toHaveProperty("ai_coach");
    expect(result).toHaveProperty("calendar_intelligence");
    expect(result).toHaveProperty("email_intelligence");
    expect(result).toHaveProperty("activity_intelligence");
  });
});

describe("getEmployeeScore — contract", () => {
  it("returns EmployeeScoreResponse", async () => {
    const payload = {
      score: 82,
      trend: "up",
      confidence: 0.9,
      factors: [
        {
          name: "engagement",
          contribution: 12,
          signal_type: "activity",
          label: "التفاعل",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEmployeeScore("e-1", TENANT);

    expect(typeof result.score).toBe("number");
    expect(["up", "down", "stable"]).toContain(result.trend);
    expect(Array.isArray(result.factors)).toBe(true);
  });
});

describe("getEmployeeTimeline — contract", () => {
  it("returns EmployeeTimelineResponse with cursor pagination", async () => {
    const payload = {
      events: [
        {
          id: "ev-1",
          action: "created",
          title: "تم الإنشاء",
          source: "crm",
          source_label: "CRM",
          timestamp: "2026-07-16T00:00:00Z",
          actor: "خالد",
        },
      ],
      next_cursor: "cursor-1",
      has_next: true,
      total: 25,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEmployeeTimeline("e-1", {}, TENANT);

    expect(Array.isArray(result.events)).toBe(true);
    expect(typeof result.has_next).toBe("boolean");
    expect(typeof result.total).toBe("number");
  });
});

describe("bulkEditEmployees — contract", () => {
  it("returns { updated: number }", async () => {
    mockAxios.patch.mockResolvedValueOnce(mockResponse({ updated: 5 }));

    const result = await bulkEditEmployees({ department: "sales" }, TENANT);

    expect(typeof result.updated).toBe("number");
    expect(result.updated).toBe(5);
  });
});

describe("bulkDeleteEmployees — contract", () => {
  it("returns { deleted: number }", async () => {
    mockAxios.post.mockResolvedValueOnce(mockResponse({ deleted: 3 }));

    const result = await bulkDeleteEmployees(["e-1", "e-2", "e-3"], TENANT);

    expect(typeof result.deleted).toBe("number");
  });
});

describe("exportEmployees — contract", () => {
  it("returns Blob", async () => {
    mockAxios.get.mockResolvedValueOnce(
      mockResponse(new Blob(["csv-data"], { type: "text/csv" })),
    );

    const result = await exportEmployees({}, TENANT);

    expect(result).toBeInstanceOf(Blob);
    const callConfig = mockAxios.get.mock.calls[0];
    expect(callConfig[1].responseType).toBe("blob");
  });
});

// ─── Search API Contracts ─────────────────────────────────────

describe("unifiedSearch — contract", () => {
  it("returns SearchResponse with items, facets, suggestions", async () => {
    const payload = {
      query: "أرامكو",
      strategy: "hybrid",
      total: 10,
      took_ms: 150,
      items: [
        {
          id: "r-1",
          type: "company",
          score: 0.95,
          data: {},
          matched_fields: ["name_ar"],
          explanation: null,
        },
      ],
      facets: { industry: { energy: 5 } },
      suggestions: ["أرامكو السعودية"],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await unifiedSearch(
      { q: "أرامكو", strategy: "hybrid" },
      TENANT,
    );

    expect(result.query).toBe("أرامكو");
    expect(result.strategy).toBe("hybrid");
    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.took_ms).toBe("number");
  });

  it("omits facets when include_facets is false", async () => {
    mockAxios.get.mockResolvedValueOnce(
      mockResponse({
        query: "test",
        strategy: "fulltext",
        total: 0,
        took_ms: 5,
        items: [],
      }),
    );

    await unifiedSearch({ q: "test", strategy: "fulltext" }, TENANT);

    const params = mockAxios.get.mock.calls[0][1].params;
    expect(params.include_facets).toBeUndefined();
  });
});

// ─── Executive Dashboard Contracts ────────────────────────────

describe("getExecutiveDashboard — contract", () => {
  it("returns ExecutiveDashboardResponse", async () => {
    const payload = {
      revenue: {
        total_booked: 1000000,
        total_pipeline: 5000000,
        weighted_pipeline: 2500000,
        forecast: 3000000,
        growth_percent: 15,
      },
      team: {
        total_employees: 50,
        active_employees: 45,
        top_performers: [],
        avg_win_rate: 0.42,
      },
      risk: {
        expiring_contracts: 3,
        stalled_deals: 5,
        inactive_companies: 10,
        low_pipeline_employees: 2,
      },
      health: {
        overall_health: "good",
        data_completeness: 0.85,
        sync_status: "ok",
        last_activity: "2026-07-16",
      },
      pipeline: {
        total_deals: 30,
        total_value: 5000000,
        won_deals: 10,
        lost_deals: 5,
        win_rate: 0.33,
        avg_deal_size: 166666,
        by_stage: [],
      },
      renewals: {
        due_next_30_days: 2,
        due_next_90_days: 5,
        total_renewal_value: 200000,
        at_risk: [],
      },
      growth: {
        new_companies_30d: 8,
        new_contacts_30d: 25,
        new_opportunities_30d: 12,
        new_contracts_30d: 4,
      },
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getExecutiveDashboard(TENANT);

    expect(result).toHaveProperty("revenue");
    expect(result).toHaveProperty("team");
    expect(result).toHaveProperty("risk");
    expect(result).toHaveProperty("health");
    expect(result).toHaveProperty("pipeline");
    expect(result).toHaveProperty("renewals");
    expect(result).toHaveProperty("growth");
    expect(typeof result.revenue.total_booked).toBe("number");
  });
});

// ─── Opportunity / Pipeline Contracts ─────────────────────────

describe("listOpportunities — contract", () => {
  it("returns OpportunityListResponse", async () => {
    const payload = {
      items: [
        {
          id: "opp-1",
          name: "صفقة أرامكو",
          stage: "proposal",
          value: 500000,
          company_id: "c-1",
          probability: 0.6,
          expected_close_date: "2026-08-01",
        },
      ],
      total: 1,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listOpportunities(TENANT);

    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.total).toBe("number");
    expect(result.items[0]).toHaveProperty("stage");
    expect(result.items[0]).toHaveProperty("value");
  });
});

describe("createOpportunity — contract", () => {
  it("returns created Opportunity", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({
        id: "opp-new",
        name: "صفقة جديدة",
        stage: "qualification",
        value: 100000,
        company_id: "c-1",
      }),
    );

    const result = await createOpportunity(TENANT, "c-1", "صفقة جديدة", 100000);

    expect(result.id).toBe("opp-new");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/opportunities",
      null,
      expect.anything(),
    );
  });
});

describe("listPipelines — contract", () => {
  it("returns PipelineListResponse", async () => {
    mockAxios.get.mockResolvedValueOnce(
      mockResponse({
        items: [{ id: "p-1", name: "Pipeline رئيسي", stages: 5 }],
      }),
    );

    const result = await listPipelines(TENANT);

    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("stages");
  });
});

// ─── Activity Contracts ───────────────────────────────────────

describe("getEntityActivities — contract", () => {
  it("returns EntityActivityResponse", async () => {
    const payload = {
      entity_type: "company",
      entity_id: "c-1",
      items: [
        {
          id: "a-1",
          tenant_id: TENANT,
          actor: "user-1",
          action: "created",
          entity_type: "company",
          entity_id: "c-1",
          timestamp: "2026-07-16T00:00:00Z",
        },
      ],
      total: 1,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEntityActivities("company", "c-1", TENANT);

    expect(result.entity_type).toBe("company");
    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.total).toBe("number");
  });
});

// ─── Auth Contracts ───────────────────────────────────────────

describe("login — contract", () => {
  it("returns tokens and stores them", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({
        access_token: "at_123",
        refresh_token: "rt_123",
        token_type: "bearer",
      }),
    );

    const result = await login("user@test.com", "pass");

    expect(result).toHaveProperty("access_token");
    expect(localStorage.getItem("access_token")).toBe("at_123");
    expect(localStorage.getItem("refresh_token")).toBe("rt_123");
  });
});

describe("register — contract", () => {
  it("returns tokens and stores them", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({
        access_token: "at_456",
        refresh_token: "rt_456",
        token_type: "bearer",
      }),
    );

    const result = await register("new@test.com", "pass", "خالد");

    expect(result).toHaveProperty("access_token");
    expect(localStorage.getItem("access_token")).toBe("at_456");
  });
});

describe("getCurrentUser — contract", () => {
  it("returns UserProfile", async () => {
    const payload = {
      id: "u-1",
      email: "user@test.com",
      full_name: "خالد",
      full_name_ar: null,
      role: "admin",
      is_active: true,
      is_verified: true,
      tenant_id: TENANT,
      created_at: "2026-01-01",
      updated_at: "2026-07-16",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getCurrentUser();

    expect(result).toHaveProperty("email");
    expect(result).toHaveProperty("role");
    expect(result).toHaveProperty("tenant_id");
  });
});

describe("changePassword — contract", () => {
  it("returns { message: string }", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ message: "تم تغيير كلمة المرور" }),
    );

    const result = await changePassword("old", "new");

    expect(typeof result.message).toBe("string");
  });
});

// ─── Company 360 Contracts ────────────────────────────────────

describe("getCompany360 — contract", () => {
  it("returns Company360Response with all sections", async () => {
    const payload = {
      company: {
        id: "c-1",
        name_ar: "أرامكو",
        name_en: null,
        cr_number: "101",
        status: "نشط",
        city: null,
        region: null,
        phone: null,
        email: null,
        confidence_score: null,
        created_at: "2026-01-01",
        updated_at: "2026-07-16",
        branches: [],
        licenses: [],
        contacts: [],
      },
      overview: {
        total_contacts: 10,
        total_opportunities: 5,
        total_revenue: 1000000,
        active_contracts: 2,
        pending_tasks: 3,
        upcoming_meetings: 1,
        last_activity: null,
        signal_count: 8,
        contacts_page: 1,
        contacts_total: 10,
        opportunities_page: 1,
        opportunities_total: 5,
        timeline_page: 1,
        timeline_total: 20,
      },
      organization: {
        branches: [],
        departments: [],
        employees_count: 0,
        legal_form: null,
        incorporation_date: null,
      },
      contacts: [],
      assigned_employees: [],
      opportunities: [],
      contracts: [],
      invoices: [],
      timeline: [],
      documents: [],
      emails: [],
      meetings: [],
      tasks: [],
      signals: { items: [], total: 0 },
      branches: [],
      licenses: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getCompany360("c-1", TENANT);

    expect(result).toHaveProperty("company");
    expect(result).toHaveProperty("overview");
    expect(result).toHaveProperty("organization");
    expect(result).toHaveProperty("signals");
  });
});

// ─── DLQ Contracts ────────────────────────────────────────────

describe("listDlq — contract", () => {
  it("returns PaginatedResponse<DlqEntry>", async () => {
    const payload = {
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: 1,
          source_slug: "scraper",
          cr_number: "101",
          stage: "enrichment",
          error_message: "timeout",
          error_type: "TimeoutError",
          retry_count: 1,
          max_retries: 3,
          status: "failed",
          created_at: "2026-07-16",
          last_retry_at: null,
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listDlq(TENANT);

    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.total).toBe("number");
    expect(result.items[0]).toHaveProperty("stage");
    expect(result.items[0]).toHaveProperty("error_message");
  });
});

describe("retryDlq — contract", () => {
  it("returns DlqRetryResponse", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ processed: 10, retried: 5, resolved: 3, still_failed: 2 }),
    );

    const result = await retryDlq(TENANT, 50);

    expect(typeof result.processed).toBe("number");
    expect(typeof result.retried).toBe("number");
    expect(typeof result.resolved).toBe("number");
  });
});

describe("purgeDlq — contract", () => {
  it("returns { purged: number }", async () => {
    mockAxios.delete.mockResolvedValueOnce(mockResponse({ purged: 8 }));

    const result = await purgeDlq(TENANT, "resolved");

    expect(typeof result.purged).toBe("number");
  });
});

// ─── Entity Resolution Contracts ──────────────────────────────

describe("listGoldenRecords — contract", () => {
  it("returns PaginatedResponse<GoldenRecordAdmin>", async () => {
    const payload = {
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: "gr-1",
          tenant_id: TENANT,
          cr_number: "101",
          company_name_ar: "أرامكو",
          status: "clean",
          confidence_score: 0.95,
          source_records: 3,
          created_at: "2026-07-16",
          updated_at: "2026-07-16",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listGoldenRecords(TENANT);

    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("source_records");
  });
});

describe("listConflicts — contract", () => {
  it("returns PaginatedResponse<EntityResolutionConflict>", async () => {
    const payload = {
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: "cf-1",
          tenant_id: TENANT,
          cr_number_a: "101",
          cr_number_b: "102",
          status: "pending",
          reason: "duplicate_cr",
          created_at: "2026-07-16",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listConflicts(TENANT);

    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("cr_number_a");
  });
});

// ─── Tasks Contracts ──────────────────────────────────────────

describe("listTasks — contract", () => {
  it("returns TaskResponse[]", async () => {
    const payload = [
      {
        id: "t-1",
        title: "متابعة أرامكو",
        priority: "high",
        source: "copilot",
        company_id: "c-1",
        completed: false,
        created_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listTasks(TENANT, "high");

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("priority");
    expect(result[0]).toHaveProperty("completed");
  });
});

describe("completeTask — contract", () => {
  it("returns completed TaskResponse", async () => {
    mockAxios.put.mockResolvedValueOnce(
      mockResponse({
        id: "t-1",
        title: "متابعة",
        priority: "high",
        source: "copilot",
        completed: true,
      }),
    );

    const result = await completeTask("t-1");

    expect(result.completed).toBe(true);
  });
});

// ─── Copilot Contracts ────────────────────────────────────────

describe("submitCopilotFeedback — contract", () => {
  it("returns CopilotFeedbackResponse", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ success: true, helpful_rate: 0.85, total_ratings: 20 }),
    );

    const result = await submitCopilotFeedback(
      { message_id: "msg-1", rating: "positive" },
      TENANT,
    );

    expect(result.success).toBe(true);
    expect(typeof result.helpful_rate).toBe("number");
  });
});

describe("getCopilotTelemetry — contract", () => {
  it("returns CopilotTelemetryData with all sections", async () => {
    const payload = {
      summary: {
        total_calls: 100,
        success_rate: 0.92,
        avg_latency_ms: 250,
        p95_latency_ms: 500,
      },
      tools: [],
      latency_distribution: [],
      result_histogram: [],
      volume_over_time: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getCopilotTelemetry(TENANT, 7);

    expect(result).toHaveProperty("summary");
    expect(result).toHaveProperty("tools");
    expect(Array.isArray(result.latency_distribution)).toBe(true);
  });
});

// ─── Admin API Contracts ──────────────────────────────────────

describe("listAdminTenants — contract", () => {
  it("returns AdminTenantListItem[]", async () => {
    const payload = [
      {
        id: "t-1",
        name: "SalesOS",
        slug: "salesos",
        domain: null,
        plan: "enterprise",
        is_active: true,
        user_count: 10,
        created_at: "2026-01-01",
        updated_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminTenants();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("slug");
    expect(result[0]).toHaveProperty("user_count");
  });
});

describe("listAdminPlans — contract", () => {
  it("returns AdminPlan[]", async () => {
    const payload = [
      {
        id: "p-1",
        name: "Enterprise",
        tier: "enterprise",
        price_monthly: 999,
        price_yearly: 9990,
        max_users: 100,
        max_storage_mb: 10000,
        max_api_calls: 1000000,
        features: ["sso", "api"],
        is_active: true,
        created_at: "2026-01-01",
        updated_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminPlans();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("tier");
    expect(result[0]).toHaveProperty("features");
  });
});

describe("listAdminUsers — contract", () => {
  it("returns AdminUser[]", async () => {
    const payload = [
      {
        id: "u-1",
        email: "admin@test.com",
        full_name: "Admin",
        full_name_ar: null,
        role: "admin",
        is_active: true,
        is_verified: true,
        tenant_id: TENANT,
        tenant_name: "SalesOS",
        created_at: "2026-01-01",
        last_login_at: null,
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminUsers();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("tenant_name");
  });
});

describe("getAdminDetailedHealth — contract", () => {
  it("returns AdminDetailedHealth", async () => {
    const payload = {
      overall_status: "healthy",
      uptime_seconds: 86400,
      components: [
        {
          component: "database",
          status: "healthy",
          latency_ms: 5,
          last_check: "2026-07-16T00:00:00Z",
          details: null,
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminDetailedHealth();

    expect(result).toHaveProperty("overall_status");
    expect(Array.isArray(result.components)).toBe(true);
    expect(result.components[0]).toHaveProperty("latency_ms");
  });
});

describe("getAdminAICostSummary — contract", () => {
  it("returns AdminAICostSummary", async () => {
    const payload = {
      total_cost: 150.5,
      total_tokens: 500000,
      by_model: [],
      by_tenant: [],
      by_operation: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminAICostSummary(30);

    expect(typeof result.total_cost).toBe("number");
    expect(Array.isArray(result.by_model)).toBe(true);
    expect(Array.isArray(result.by_tenant)).toBe(true);
  });
});

describe("listAdminAuditLogs — contract", () => {
  it("returns PaginatedResponse<AuditLogEntry>", async () => {
    const payload = {
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: "al-1",
          action: "login",
          action_type: "auth",
          actor_id: "u-1",
          actor_name: "Admin",
          actor_email: "admin@test.com",
          resource: "session",
          resource_type: "auth",
          resource_id: "s-1",
          tenant_id: TENANT,
          tenant_name: "SalesOS",
          details: null,
          ip_address: "127.0.0.1",
          user_agent: null,
          created_at: "2026-07-16",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminAuditLogs();

    expect(Array.isArray(result.items)).toBe(true);
    expect(result.items[0]).toHaveProperty("actor_email");
    expect(result.items[0]).toHaveProperty("ip_address");
  });
});

// ─── Error Handling Contracts ─────────────────────────────────
// Note: Interceptor behavior (401 redirect, 403 warn) is tested in api.test.tsx.
// Contract tests verify API function response shapes and error propagation.

describe("error handling — error propagation", () => {
  it("propagates axios errors when API call fails", async () => {
    const apiError = new Error("Request failed with status code 500");
    (apiError as any).response = {
      status: 500,
      data: { detail: "Internal Server Error" },
    };
    mockAxios.get.mockRejectedValueOnce(apiError);

    await expect(getCompany("c-1", TENANT)).rejects.toThrow(
      "Request failed with status code 500",
    );
  });

  it("propagates network errors", async () => {
    const networkError = new Error("Network Error");
    mockAxios.get.mockRejectedValueOnce(networkError);

    await expect(searchCompanies({ q: "test" }, TENANT)).rejects.toThrow(
      "Network Error",
    );
  });

  it("propagates 4xx errors with error data", async () => {
    const apiError = new Error("Request failed with status code 400");
    (apiError as any).response = {
      status: 400,
      data: { detail: "Bad request", errors: { field: "name" } },
    };
    mockAxios.post.mockRejectedValueOnce(apiError);

    await expect(
      createCompany({ name_ar: "", cr_number: "" }, TENANT),
    ).rejects.toThrow("Request failed with status code 400");
  });

  it("propagates 422 validation errors", async () => {
    const apiError = new Error("Request failed with status code 422");
    (apiError as any).response = {
      status: 422,
      data: {
        detail: [
          {
            loc: ["body", "email"],
            msg: "field required",
            type: "value_error",
          },
        ],
      },
    };
    mockAxios.post.mockRejectedValueOnce(apiError);

    await expect(createContact({ name: "" }, TENANT)).rejects.toThrow(
      "Request failed with status code 422",
    );
  });
});

// ─── Missing API Contract Tests (Phase 17) ─────────────────────

describe("getMy360 — contract", () => {
  it("returns Employee360Response for current user", async () => {
    const payload = {
      profile: {
        id: "e-1",
        full_name: "خالد",
        full_name_ar: null,
        email: "k@test.com",
        role: "admin",
        phone: null,
        avatar_url: null,
        is_active: true,
        tenant_id: TENANT,
        created_at: "2026-01-01",
        team: [],
        manager: null,
      },
      portfolio: {
        companies: [],
        contacts: [],
        pipeline: [],
        revenue: 0,
        contracts: [],
        projects: [],
      },
      calendar_intelligence: {
        today_count: 0,
        week_count: 0,
        month_count: 0,
        total_hours: 0,
        avg_duration_minutes: 0,
        unique_companies_met: 0,
        upcoming: [],
      },
      email_intelligence: {
        sent: 0,
        received: 0,
        replies: 0,
        avg_response_hours: 0,
        top_contacts: [],
        top_companies: [],
      },
      activity_intelligence: {
        meetings: 0,
        emails: 0,
        calls: 0,
        tasks: 0,
        notes: 0,
        documents: 0,
        total: 0,
        recent: [],
      },
      kpis: {
        revenue: 0,
        pipeline: 0,
        win_rate: 0,
        response_rate: 0,
        follow_up_rate: 0,
        activities: 0,
        productivity: 0,
        forecast: 0,
      },
      ai_coach: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getMy360(TENANT);

    expect(result).toHaveProperty("profile");
    expect(result).toHaveProperty("kpis");
    expect(result).toHaveProperty("ai_coach");
    expect(mockAxios.get).toHaveBeenCalledWith(
      "/api/v1/employees/me/360",
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

describe("getEmployeeSignals — contract", () => {
  it("returns EmployeeSignalsResponse", async () => {
    const payload = {
      by_type: [{ type: "meeting", count: 5, label: "اجتماع" }],
      by_source: [{ source: "crm", count: 3, label: "CRM" }],
      trend: [{ date: "2026-07-16", count: 2 }],
      total: 10,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEmployeeSignals("e-1", TENANT);

    expect(Array.isArray(result.by_type)).toBe(true);
    expect(Array.isArray(result.by_source)).toBe(true);
    expect(Array.isArray(result.trend)).toBe(true);
    expect(typeof result.total).toBe("number");
  });
});

describe("getEmployeePerformance — contract", () => {
  it("returns EmployeePerformanceResponse", async () => {
    const payload = {
      score_trend: [
        { date: "2026-07-10", score: 80 },
        { date: "2026-07-16", score: 82 },
      ],
      peer_comparison: [
        {
          metric: "pipeline",
          employee_value: 500000,
          department_avg: 350000,
          label: "Pipeline",
        },
      ],
      risk_flags: [
        {
          type: "stalled",
          label: "صفقة متوقفة",
          severity: "medium",
          description: "No activity in 30 days",
        },
      ],
      factors: [
        {
          name: "engagement",
          contribution: 12,
          signal_type: "activity",
          label: "التفاعل",
        },
      ],
      current_score: 82,
      score_trend_direction: "up",
      department: "sales",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getEmployeePerformance("e-1", TENANT);

    expect(Array.isArray(result.score_trend)).toBe(true);
    expect(Array.isArray(result.risk_flags)).toBe(true);
    expect(typeof result.current_score).toBe("number");
    expect(["up", "down", "stable"]).toContain(result.score_trend_direction);
  });
});

describe("addCompanyContact — contract", () => {
  it("returns Contact via company endpoint", async () => {
    const payload = {
      id: "ct-new",
      name: "مريم",
      email: "m@test.com",
      phone: null,
      position: "محاسبة",
      company_id: "c-1",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await addCompanyContact(
      "c-1",
      { name: "مريم", position: "محاسبة" },
      TENANT,
    );

    expect(result).toHaveProperty("id");
    expect(result.name).toBe("مريم");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/companies/c-1/contacts",
      expect.anything(),
      expect.objectContaining({
        headers: { "X-Tenant-Id": TENANT },
      }),
    );
  });
});

describe("advanceOpportunity — contract", () => {
  it("posts to advance stage", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({
        id: "opp-1",
        stage: "negotiation",
        name: "صفقة",
        company_id: "c-1",
      }),
    );

    const result = await advanceOpportunity("opp-1", "negotiation");

    expect(result.stage).toBe("negotiation");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/opportunities/opp-1/advance",
      null,
      expect.objectContaining({
        params: { to_stage: "negotiation" },
      }),
    );
  });
});

describe("closeWon — contract", () => {
  it("posts to won endpoint", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ id: "opp-1", stage: "closed_won", won_amount: 500000 }),
    );

    const result = await closeWon("opp-1", 500000);

    expect(result.stage).toBe("closed_won");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/opportunities/opp-1/won",
      null,
      expect.objectContaining({
        params: { amount: 500000 },
      }),
    );
  });

  it("works without amount", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ id: "opp-1", stage: "closed_won" }),
    );

    const result = await closeWon("opp-1");

    expect(result.stage).toBe("closed_won");
  });
});

describe("closeLost — contract", () => {
  it("posts to lost endpoint", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({
        id: "opp-1",
        stage: "closed_lost",
        loss_reason: "budget",
      }),
    );

    const result = await closeLost("opp-1", "budget");

    expect(result.stage).toBe("closed_lost");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/opportunities/opp-1/lost",
      null,
      expect.objectContaining({
        params: { reason: "budget" },
      }),
    );
  });
});

describe("getGlobalActivities — contract", () => {
  it("returns ActivityQueryResponse", async () => {
    const payload = {
      items: [
        {
          id: "a-1",
          tenant_id: TENANT,
          actor: "user-1",
          action: "created",
          entity_type: "company",
          entity_id: "c-1",
          timestamp: "2026-07-16T00:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getGlobalActivities(TENANT, { action: "created" });

    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.total).toBe("number");
    expect(typeof result.limit).toBe("number");
  });
});

describe("queryActivities — contract", () => {
  it("returns ActivityQueryResponse with query params", async () => {
    const payload = { items: [], total: 0, limit: 10, offset: 0 };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await queryActivities(
      { entity_type: "company", limit: 10 },
      TENANT,
    );

    expect(result.total).toBe(0);
    expect(mockAxios.get).toHaveBeenCalledWith(
      "/api/v1/activities",
      expect.objectContaining({
        params: { entity_type: "company", limit: 10 },
      }),
    );
  });
});

describe("createTask — contract", () => {
  it("returns created TaskResponse", async () => {
    const payload = {
      id: "t-new",
      title: "مهمة جديدة",
      priority: "high",
      source: "manual",
      company_id: null,
      completed: false,
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createTask(TENANT, "مهمة جديدة", "high");

    expect(result).toHaveProperty("id");
    expect(result.title).toBe("مهمة جديدة");
    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/tasks",
      expect.objectContaining({ title: "مهمة جديدة" }),
      expect.anything(),
    );
  });
});

describe("getDlqStats — contract", () => {
  it("returns failed_by_stage map", async () => {
    mockAxios.get.mockResolvedValueOnce(
      mockResponse({ failed_by_stage: { enrichment: 5, validation: 2 } }),
    );

    const result = await getDlqStats(TENANT);

    expect(result).toHaveProperty("failed_by_stage");
    expect(typeof result.failed_by_stage.enrichment).toBe("number");
  });
});

// ─── Admin API Contracts (Phase 17 additions) ───────────────────

describe("getAdminTenant — contract", () => {
  it("returns AdminTenantDetail", async () => {
    const payload = {
      id: "t-1",
      name: "SalesOS",
      slug: "salesos",
      domain: null,
      plan: "enterprise",
      is_active: true,
      settings: {},
      features: {},
      user_count: 10,
      subscription_ends_at: null,
      created_at: "2026-01-01",
      updated_at: "2026-07-16",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminTenant("t-1");

    expect(result).toHaveProperty("slug");
    expect(result).toHaveProperty("settings");
    expect(result).toHaveProperty("features");
  });
});

describe("createAdminTenant — contract", () => {
  it("returns created AdminTenantDetail", async () => {
    const payload = {
      id: "t-new",
      name: "NewCo",
      slug: "newco",
      domain: null,
      plan: "starter",
      is_active: true,
      settings: {},
      features: {},
      user_count: 0,
      subscription_ends_at: null,
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createAdminTenant({ name: "NewCo", slug: "newco" });

    expect(result.name).toBe("NewCo");
    expect(mockAxios.post).toHaveBeenCalledWith("/api/v1/admin/tenants", {
      name: "NewCo",
      slug: "newco",
    });
  });
});

describe("updateAdminTenant — contract", () => {
  it("PUTs and returns updated detail", async () => {
    const payload = {
      id: "t-1",
      name: "UpdatedCo",
      slug: "salesos",
      domain: null,
      plan: "enterprise",
      is_active: true,
      settings: {},
      features: {},
      user_count: 10,
      subscription_ends_at: null,
      created_at: "2026-01-01",
      updated_at: "2026-07-16",
    };
    mockAxios.put.mockResolvedValueOnce(mockResponse(payload));

    const result = await updateAdminTenant("t-1", { name: "UpdatedCo" });

    expect(result.name).toBe("UpdatedCo");
  });
});

describe("deleteAdminTenant — contract", () => {
  it("sends DELETE and returns void", async () => {
    mockAxios.delete.mockResolvedValueOnce(mockResponse(undefined));

    await deleteAdminTenant("t-1");

    expect(mockAxios.delete).toHaveBeenCalledWith("/api/v1/admin/tenants/t-1");
  });
});

describe("getAdminTenantUsage — contract", () => {
  it("returns AdminTenantUsage", async () => {
    const payload = {
      tenant_id: "t-1",
      tenant_name: "SalesOS",
      api_calls: 5000,
      storage_mb: 250,
      active_users: 8,
      total_users: 10,
      period_start: "2026-07-01",
      period_end: "2026-07-31",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminTenantUsage("t-1");

    expect(typeof result.api_calls).toBe("number");
    expect(typeof result.storage_mb).toBe("number");
  });
});

describe("listAdminLicenses — contract", () => {
  it("returns AdminLicense[]", async () => {
    const payload = [
      {
        id: "l-1",
        tenant_id: "t-1",
        tenant_name: "SalesOS",
        plan_id: "p-1",
        plan_name: "Enterprise",
        tier: "enterprise",
        is_active: true,
        starts_at: null,
        ends_at: null,
        created_at: "2026-01-01",
        updated_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminLicenses();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("plan_name");
    expect(result[0]).toHaveProperty("tier");
  });
});

describe("createAdminLicense — contract", () => {
  it("returns created AdminLicense", async () => {
    const payload = {
      id: "l-new",
      tenant_id: "t-1",
      tenant_name: "NewCo",
      plan_id: "p-1",
      plan_name: "Starter",
      tier: "starter",
      is_active: true,
      starts_at: "2026-07-16",
      ends_at: null,
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createAdminLicense({
      tenant_id: "t-1",
      plan_id: "p-1",
    });

    expect(result).toHaveProperty("id");
    expect(mockAxios.post).toHaveBeenCalledWith("/api/v1/admin/licenses", {
      tenant_id: "t-1",
      plan_id: "p-1",
    });
  });
});

describe("getAdminUser — contract", () => {
  it("returns AdminUserDetail", async () => {
    const payload = {
      id: "u-1",
      email: "admin@test.com",
      full_name: "Admin",
      full_name_ar: null,
      role: "admin",
      is_active: true,
      is_verified: true,
      tenant_id: TENANT,
      tenant_name: "SalesOS",
      created_at: "2026-01-01",
      last_login_at: null,
      permissions: ["read", "write"],
      updated_at: "2026-07-16",
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminUser("u-1");

    expect(Array.isArray(result.permissions)).toBe(true);
    expect(result).toHaveProperty("last_login_at");
  });
});

describe("listAdminInvoices — contract", () => {
  it("returns AdminInvoice[]", async () => {
    const payload = [
      {
        id: "inv-1",
        tenant_id: "t-1",
        tenant_name: "SalesOS",
        amount: 999,
        currency: "SAR",
        status: "paid",
        description: "Monthly subscription",
        due_date: null,
        paid_at: "2026-07-01",
        created_at: "2026-07-01",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminInvoices();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("amount");
    expect(result[0]).toHaveProperty("status");
  });
});

describe("listAdminTransactions — contract", () => {
  it("returns AdminTransaction[]", async () => {
    const payload = [
      {
        id: "tr-1",
        tenant_id: "t-1",
        tenant_name: "SalesOS",
        amount: 999,
        currency: "SAR",
        status: "completed",
        method: "card",
        description: "Payment",
        reference: null,
        created_at: "2026-07-01",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminTransactions("t-1");

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("method");
  });
});

describe("createAdminFeatureFlag — contract", () => {
  it("returns created AdminFeatureFlag", async () => {
    const payload = {
      id: "ff-1",
      key: "new-dashboard",
      name: "New Dashboard",
      description: null,
      enabled: false,
      is_global: false,
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createAdminFeatureFlag({
      key: "new-dashboard",
      name: "New Dashboard",
    });

    expect(result.key).toBe("new-dashboard");
    expect(result.enabled).toBe(false);
  });
});

describe("updateAdminFeatureFlag — contract", () => {
  it("returns updated AdminFeatureFlag", async () => {
    const payload = {
      id: "ff-1",
      key: "new-dashboard",
      name: "New Dashboard",
      description: null,
      enabled: true,
      is_global: false,
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
    };
    mockAxios.put.mockResolvedValueOnce(mockResponse(payload));

    const result = await updateAdminFeatureFlag("ff-1", { enabled: true });

    expect(result.enabled).toBe(true);
  });
});

describe("getAdminFlagTenants — contract", () => {
  it("returns AdminFlagTenant[]", async () => {
    const payload = [
      {
        flag_id: "ff-1",
        flag_key: "new-dashboard",
        tenant_id: "t-1",
        tenant_name: "SalesOS",
        enabled: true,
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminFlagTenants("ff-1");

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("tenant_name");
  });
});

describe("toggleAdminFlagForTenant — contract", () => {
  it("PUTs tenant flag toggle", async () => {
    mockAxios.put.mockResolvedValueOnce(mockResponse(undefined));

    await toggleAdminFlagForTenant("ff-1", "t-1", true);

    expect(mockAxios.put).toHaveBeenCalledWith(
      "/api/v1/admin/feature-flags/ff-1/tenants/t-1",
      { enabled: true },
    );
  });
});

describe("listAdminJobs — contract", () => {
  it("returns AdminJob[]", async () => {
    const payload = [
      {
        id: "job-1",
        type: "enrichment",
        status: "completed",
        progress: 100,
        tenant_id: null,
        created_by: null,
        payload: {},
        result: {},
        error_message: null,
        retry_count: 0,
        max_retries: 3,
        scheduled_at: null,
        started_at: null,
        completed_at: "2026-07-16",
        created_at: "2026-07-16",
        updated_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminJobs();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("type");
    expect(result[0]).toHaveProperty("status");
  });
});

describe("getAdminJob — contract", () => {
  it("returns AdminJobDetail with logs", async () => {
    const payload = {
      id: "job-1",
      type: "enrichment",
      status: "completed",
      progress: 100,
      tenant_id: null,
      created_by: null,
      payload: {},
      result: {},
      error_message: null,
      retry_count: 0,
      max_retries: 3,
      scheduled_at: null,
      started_at: null,
      completed_at: "2026-07-16",
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
      logs: [
        {
          level: "info",
          message: "started",
          timestamp: "2026-07-16T00:00:00Z",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminJob("job-1");

    expect(result).toHaveProperty("logs");
    expect(Array.isArray(result.logs)).toBe(true);
  });
});

describe("retryAdminJob — contract", () => {
  it("POSTs retry and returns void", async () => {
    mockAxios.post.mockResolvedValueOnce(mockResponse(undefined));

    await retryAdminJob("job-1");

    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/admin/jobs/job-1/retry",
    );
  });
});

describe("listAdminAICosts — contract", () => {
  it("returns AdminAICost[]", async () => {
    const payload = [
      {
        id: "ai-1",
        model: "gpt-4",
        tenant_id: null,
        tenant_name: null,
        prompt_tokens: 500,
        completion_tokens: 200,
        total_tokens: 700,
        cost: 0.05,
        operation: "search",
        created_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminAICosts();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("model");
    expect(typeof result[0].cost).toBe("number");
  });
});

describe("getAdminAIUsage — contract", () => {
  it("returns AdminAIUsage", async () => {
    const payload = {
      total_prompt_tokens: 5000,
      total_completion_tokens: 2000,
      total_tokens: 7000,
      by_model: [],
      by_tenant: [],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminAIUsage(30);

    expect(typeof result.total_tokens).toBe("number");
    expect(Array.isArray(result.by_model)).toBe(true);
  });
});

describe("getAdminHealthHistory — contract", () => {
  it("returns health history entries", async () => {
    const payload = [
      {
        timestamp: "2026-07-16T00:00:00Z",
        overall_status: "healthy",
        components: { database: "healthy" },
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminHealthHistory(24);

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("overall_status");
    expect(result[0]).toHaveProperty("components");
  });
});

describe("listAdminPermissions — contract", () => {
  it("returns AdminPermission[]", async () => {
    const payload = [
      {
        id: "perm-1",
        key: "companies.read",
        name: "Read Companies",
        description: null,
        group: "companies",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminPermissions();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("key");
    expect(result[0]).toHaveProperty("group");
  });
});

describe("listAdminRoles — contract", () => {
  it("returns AdminRole[]", async () => {
    const payload = [
      {
        id: "role-1",
        name: "Admin",
        description: "Full access",
        permissions: ["*"],
        is_system: true,
        user_count: 3,
        created_at: "2026-01-01",
        updated_at: "2026-07-16",
      },
    ];
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await listAdminRoles();

    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toHaveProperty("permissions");
    expect(result[0]).toHaveProperty("user_count");
  });
});

describe("createAdminRole — contract", () => {
  it("returns created AdminRole", async () => {
    const payload = {
      id: "role-new",
      name: "Manager",
      description: "Manager role",
      permissions: ["companies.read"],
      is_system: false,
      user_count: 0,
      created_at: "2026-07-16",
      updated_at: "2026-07-16",
    };
    mockAxios.post.mockResolvedValueOnce(mockResponse(payload));

    const result = await createAdminRole({
      name: "Manager",
      permissions: ["companies.read"],
    });

    expect(result.name).toBe("Manager");
    expect(mockAxios.post).toHaveBeenCalledWith("/api/v1/admin/roles", {
      name: "Manager",
      permissions: ["companies.read"],
    });
  });
});

describe("updateAdminRole — contract", () => {
  it("returns updated AdminRole", async () => {
    const payload = {
      id: "role-1",
      name: "Super Admin",
      description: null,
      permissions: ["*"],
      is_system: true,
      user_count: 3,
      created_at: "2026-01-01",
      updated_at: "2026-07-16",
    };
    mockAxios.put.mockResolvedValueOnce(mockResponse(payload));

    const result = await updateAdminRole("role-1", { name: "Super Admin" });

    expect(result.name).toBe("Super Admin");
  });
});

describe("deleteAdminRole — contract", () => {
  it("sends DELETE and returns void", async () => {
    mockAxios.delete.mockResolvedValueOnce(mockResponse(undefined));

    await deleteAdminRole("role-1");

    expect(mockAxios.delete).toHaveBeenCalledWith("/api/v1/admin/roles/role-1");
  });
});

describe("getAdminConfig — contract", () => {
  it("returns AdminConfigResponse", async () => {
    const payload = {
      content: "# Config",
      version: 1,
      versions: [
        {
          version: 1,
          content: "# Config",
          created_at: "2026-07-16",
          created_by: "admin",
        },
      ],
    };
    mockAxios.get.mockResolvedValueOnce(mockResponse(payload));

    const result = await getAdminConfig();

    expect(typeof result.content).toBe("string");
    expect(typeof result.version).toBe("number");
    expect(Array.isArray(result.versions)).toBe(true);
  });
});

describe("saveAdminConfig — contract", () => {
  it("PUTs and returns updated config", async () => {
    const payload = { content: "# New Config", version: 2, versions: [] };
    mockAxios.put.mockResolvedValueOnce(mockResponse(payload));

    const result = await saveAdminConfig("# New Config");

    expect(result.version).toBe(2);
    expect(mockAxios.put).toHaveBeenCalledWith("/api/v1/admin/config", {
      content: "# New Config",
    });
  });
});

describe("validateAdminConfig — contract", () => {
  it("returns validation result", async () => {
    mockAxios.post.mockResolvedValueOnce(
      mockResponse({ valid: true, errors: [] }),
    );

    const result = await validateAdminConfig("# Config");

    expect(result.valid).toBe(true);
    expect(Array.isArray(result.errors)).toBe(true);
  });
});
