import { render, screen, fireEvent } from "@testing-library/react"
import { AuditLogView } from "../AuditLogView"
import type { AuditLogEntry } from "@/lib/api"
import type { AuditLogFilters } from "../types"

const sampleEntry: AuditLogEntry = {
  id: "1",
  action: "user.created",
  action_type: "create",
  actor_id: "u1",
  actor_name: "أحمد محمد",
  actor_email: "ahmed@example.com",
  resource: "مستخدم جديد",
  resource_type: "user",
  resource_id: "u2",
  tenant_id: "t1",
  tenant_name: "شركة التقنية",
  details: { name: "خالد" },
  ip_address: "192.168.1.1",
  user_agent: "Mozilla/5.0",
  created_at: "2026-07-12T10:00:00.000Z",
}

const defaultFilters: AuditLogFilters = {
  dateFrom: undefined,
  dateTo: undefined,
  userId: undefined,
  actionType: undefined,
  resource: undefined,
  search: undefined,
  page: 1,
  pageSize: 20,
}

const defaultProps = {
  items: [sampleEntry],
  total: 1,
  loading: false,
  filters: defaultFilters,
  onFilterChange: jest.fn(),
  onExport: jest.fn(),
  onRefresh: jest.fn(),
}

function renderView(overrides?: Partial<typeof defaultProps>) {
  return render(<AuditLogView {...defaultProps} {...overrides} />)
}

describe("AuditLogView", () => {
  it("renders title", () => {
    renderView()
    expect(screen.getByText("سجل التدقيق")).toBeInTheDocument()
  })

  it("renders audit log entries", () => {
    renderView()
    expect(screen.getByText("أحمد محمد")).toBeInTheDocument()
    expect(screen.getByText("ahmed@example.com")).toBeInTheDocument()
    expect(screen.getByText("192.168.1.1")).toBeInTheDocument()
  })

  it("shows empty state when no items", () => {
    renderView({ items: [], total: 0 })
    expect(screen.getByText("لا توجد سجلات تدقيق")).toBeInTheDocument()
  })

  it("shows loading state", () => {
    renderView({ loading: true })
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument()
  })

  it("calls onExport when export button clicked", () => {
    const onExport = jest.fn()
    renderView({ onExport })
    fireEvent.click(screen.getByText("تصدير CSV"))
    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it("calls onRefresh when refresh button clicked", () => {
    const onRefresh = jest.fn()
    renderView({ onRefresh })
    fireEvent.click(screen.getByText("تحديث"))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it("toggles filter panel", () => {
    renderView()
    fireEvent.click(screen.getByText("فلتر"))
    expect(screen.getByText("إخفاء الفلتر")).toBeInTheDocument()
    fireEvent.click(screen.getByText("إخفاء الفلتر"))
    expect(screen.getByText("فلتر")).toBeInTheDocument()
  })

  it("calls onFilterChange when search typed", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const input = screen.getByPlaceholderText("بحث في السجل...")
    fireEvent.change(input, { target: { value: "ahmed" } })
    expect(onFilterChange).toHaveBeenCalledWith({ search: "ahmed", page: 1 })
  })

  it("calls onFilterChange when action type changed", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const select = screen.getByLabelText("نوع الإجراء")
    fireEvent.change(select, { target: { value: "create" } })
    expect(onFilterChange).toHaveBeenCalledWith({ actionType: "create" })
  })

  it("calls onFilterChange on pagination", () => {
    const onFilterChange = jest.fn()
    renderView({ total: 50, onFilterChange })
    const nextBtn = screen.getByLabelText("الصفحة التالية")
    fireEvent.click(nextBtn)
    expect(onFilterChange).toHaveBeenCalledWith({ page: 2 })
  })

  it("has region role with aria-label", () => {
    renderView()
    expect(screen.getByRole("region", { name: "سجل التدقيق" })).toBeInTheDocument()
  })
})
