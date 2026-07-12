import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { FeatureFlagManager } from "../FeatureFlagManager"
import type { AdminFeatureFlag } from "@/lib/api"

const sampleFlags: AdminFeatureFlag[] = [
  {
    id: "flag-1",
    key: "new_dashboard",
    name: "لوحة جديدة",
    description: "تفعيل اللوحة الجديدة",
    enabled: true,
    is_global: true,
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z",
  },
  {
    id: "flag-2",
    key: "ai_agents",
    name: "وكلاء AI",
    description: null,
    enabled: false,
    is_global: false,
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z",
  },
]

const mockMutateAsync = jest.fn().mockResolvedValue({})

jest.mock("@/lib/hooks/adminQueries", () => ({
  useAdminFeatureFlags: jest.fn(),
  useCreateAdminFeatureFlag: jest.fn(),
  useAdminFlagTenants: jest.fn(),
  useToggleAdminFlagForTenant: jest.fn(),
}))

import { useAdminFeatureFlags, useCreateAdminFeatureFlag, useAdminFlagTenants, useToggleAdminFlagForTenant } from "@/lib/hooks/adminQueries"

const mockUseAdminFeatureFlags = useAdminFeatureFlags as jest.Mock
const mockUseCreateAdminFeatureFlag = useCreateAdminFeatureFlag as jest.Mock
const mockUseAdminFlagTenants = useAdminFlagTenants as jest.Mock
const mockUseToggleAdminFlagForTenant = useToggleAdminFlagForTenant as jest.Mock

function setupFlags(flags: AdminFeatureFlag[] = sampleFlags, isLoading = false) {
  mockUseAdminFeatureFlags.mockReturnValue({ data: flags, isLoading })
  mockUseCreateAdminFeatureFlag.mockReturnValue({ mutateAsync: mockMutateAsync, isPending: false })
  mockUseAdminFlagTenants.mockReturnValue({ data: [], isLoading: false })
  mockUseToggleAdminFlagForTenant.mockReturnValue({ mutate: jest.fn(), isPending: false })
}

describe("FeatureFlagManager", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setupFlags()
  })

  it("renders title", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("الميزات التجريبية")).toBeInTheDocument()
  })

  it("renders flag list with names and keys", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("لوحة جديدة")).toBeInTheDocument()
    expect(screen.getByText("new_dashboard")).toBeInTheDocument()
    expect(screen.getByText("وكلاء AI")).toBeInTheDocument()
    expect(screen.getByText("ai_agents")).toBeInTheDocument()
  })

  it("shows enabled badge for enabled flags", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("مفعل")).toBeInTheDocument()
  })

  it("shows disabled badge for disabled flags", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("معطل")).toBeInTheDocument()
  })

  it("shows global badge for global flags", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("عام")).toBeInTheDocument()
  })

  it("shows description when present", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("تفعيل اللوحة الجديدة")).toBeInTheDocument()
  })

  it("shows loading state", () => {
    setupFlags([], true)
    render(<FeatureFlagManager />)
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument()
  })

  it("shows create new flag button", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("ميزة جديدة")).toBeInTheDocument()
  })

  it("opens create form when button clicked", () => {
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("ميزة جديدة"))
    expect(screen.getByPlaceholderText("المفتاح (key)")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("الاسم")).toBeInTheDocument()
  })

  it("calls create mutation on submit", async () => {
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("ميزة جديدة"))
    fireEvent.change(screen.getByPlaceholderText("المفتاح (key)"), { target: { value: "test_flag" } })
    fireEvent.change(screen.getByPlaceholderText("الاسم"), { target: { value: "ميزة اختبار" } })
    fireEvent.click(screen.getByText("إنشاء"))
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ key: "test_flag", name: "ميزة اختبار" })
    })
  })

  it("cancel button closes create form", () => {
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("ميزة جديدة"))
    expect(screen.getByPlaceholderText("المفتاح (key)")).toBeInTheDocument()
    fireEvent.click(screen.getByText("إلغاء"))
    expect(screen.queryByPlaceholderText("المفتاح (key)")).not.toBeInTheDocument()
  })

  it("selecting a flag shows tenant manager panel", () => {
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("لوحة جديدة"))
    expect(screen.getByText("تفعيل الميزة لكل عميل")).toBeInTheDocument()
  })

  it("selecting same flag again deselects it", () => {
    mockUseAdminFlagTenants.mockReturnValue({ data: [], isLoading: false })
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("لوحة جديدة"))
    fireEvent.click(screen.getByText("لوحة جديدة"))
    expect(screen.queryByText("تفعيل الميزة لكل عميل")).not.toBeInTheDocument()
  })

  it("shows empty tenant message when no tenants", () => {
    mockUseAdminFlagTenants.mockReturnValue({ data: [], isLoading: false })
    render(<FeatureFlagManager />)
    fireEvent.click(screen.getByText("لوحة جديدة"))
    expect(screen.getByText("لا توجد تجاوزات لهذه الميزة")).toBeInTheDocument()
  })

  it("shows placeholder when no flag selected", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("اختر ميزة لإدارة تفعيلها لكل عميل")).toBeInTheDocument()
  })

  it("displays flag count in header", () => {
    render(<FeatureFlagManager />)
    expect(screen.getByText("جميع الميزات (2)")).toBeInTheDocument()
  })
})
