import { render, screen, fireEvent } from "@testing-library/react"
import { RoleManagerView } from "../RoleManagerView"
import type { RoleItem, PermissionItem } from "../types"

const sampleRole: RoleItem = {
  id: "role-1",
  name: "مدير المبيعات",
  description: "صلاحيات مدير فريق المبيعات",
  permissions: ["companies.view", "contacts.view", "deals.manage"],
  is_system: false,
  user_count: 5,
}

const systemRole: RoleItem = {
  id: "role-sys",
  name: "مدير النظام",
  description: "دور النظام الأساسي",
  permissions: ["*"],
  is_system: true,
  user_count: 2,
}

const samplePermissions: PermissionItem[] = [
  { id: "p1", key: "companies.view", name: "عرض الشركات", description: null, group: "companies" },
  { id: "p2", key: "contacts.view", name: "عرض جهات الاتصال", description: null, group: "contacts" },
  { id: "p3", key: "deals.manage", name: "إدارة الصفقات", description: null, group: "deals" },
  { id: "p4", key: "users.view", name: "عرض المستخدمين", description: null, group: "users" },
]

const defaultProps = {
  roles: [sampleRole],
  permissions: samplePermissions,
  loading: false,
  onRefresh: jest.fn(),
  onCreateRole: jest.fn(),
  onUpdateRole: jest.fn(),
  onDeleteRole: jest.fn(),
}

function renderView(overrides?: Partial<typeof defaultProps>) {
  return render(<RoleManagerView {...defaultProps} {...overrides} />)
}

describe("RoleManagerView", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders title and region role", () => {
    renderView()
    expect(screen.getByText("إدارة الأدوار والصلاحيات")).toBeInTheDocument()
    expect(screen.getByRole("region", { name: "إدارة الأدوار" })).toBeInTheDocument()
  })

  it("renders role list with names and descriptions", () => {
    renderView()
    expect(screen.getByText("مدير المبيعات")).toBeInTheDocument()
    expect(screen.getByText("صلاحيات مدير فريق المبيعات")).toBeInTheDocument()
  })

  it("shows user count for role", () => {
    renderView()
    expect(screen.getByText("5 مستخدم")).toBeInTheDocument()
  })

  it("shows permissions for role", () => {
    renderView()
    expect(screen.getByText("companies.view")).toBeInTheDocument()
    expect(screen.getByText("contacts.view")).toBeInTheDocument()
    expect(screen.getByText("deals.manage")).toBeInTheDocument()
  })

  it("renders system role with system badge", () => {
    renderView({ roles: [systemRole] })
    expect(screen.getByText("نظامي")).toBeInTheDocument()
  })

  it("does not show edit/delete buttons for system roles", () => {
    renderView({ roles: [systemRole] })
    expect(screen.queryByLabelText("تعديل مدير النظام")).not.toBeInTheDocument()
    expect(screen.queryByLabelText("حذف مدير النظام")).not.toBeInTheDocument()
  })

  it("shows edit/delete buttons for non-system roles", () => {
    renderView()
    expect(screen.getByLabelText("تعديل مدير المبيعات")).toBeInTheDocument()
    expect(screen.getByLabelText("حذف مدير المبيعات")).toBeInTheDocument()
  })

  it("calls onDeleteRole when delete button clicked", () => {
    const onDeleteRole = jest.fn()
    renderView({ onDeleteRole })
    fireEvent.click(screen.getByLabelText("حذف مدير المبيعات"))
    expect(onDeleteRole).toHaveBeenCalledWith("role-1")
  })

  it("shows empty state when no roles", () => {
    renderView({ roles: [] })
    expect(screen.getByText("لا توجد أدوار مخصصة")).toBeInTheDocument()
    expect(screen.getByText("الأدوار النظامية غير ظاهرة هنا")).toBeInTheDocument()
  })

  it("shows loading state", () => {
    renderView({ loading: true })
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument()
  })

  it("shows create form when new role button clicked", () => {
    renderView()
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))
    expect(screen.getByRole("heading", { name: "دور جديد" })).toBeInTheDocument()
    expect(screen.getByPlaceholderText("اسم الدور")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("وصف (اختياري)")).toBeInTheDocument()
  })

  it("calls onRefresh when refresh button clicked", () => {
    const onRefresh = jest.fn()
    renderView({ onRefresh })
    fireEvent.click(screen.getByText("تحديث"))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it("permission checkboxes render in create form", () => {
    renderView()
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))
    expect(screen.getByText("عرض الشركات")).toBeInTheDocument()
    expect(screen.getByText("عرض جهات الاتصال")).toBeInTheDocument()
    expect(screen.getByText("إدارة الصفقات")).toBeInTheDocument()
  })

  it("calls onCreateRole with name and selected permissions", () => {
    const onCreateRole = jest.fn()
    renderView({ onCreateRole })
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))

    fireEvent.change(screen.getByPlaceholderText("اسم الدور"), { target: { value: "منصب جديد" } })

    const checkbox = screen.getByText("عرض الشركات").closest("label")!.querySelector("input")!
    fireEvent.click(checkbox)

    fireEvent.click(screen.getByRole("button", { name: /إنشاء/ }))
    expect(onCreateRole).toHaveBeenCalledWith({
      name: "منصب جديد",
      description: undefined,
      permissions: ["companies.view"],
    })
  })

  it("does not call onCreateRole if name is empty", () => {
    const onCreateRole = jest.fn()
    renderView({ onCreateRole })
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))
    fireEvent.click(screen.getByRole("button", { name: /إنشاء/ }))
    expect(onCreateRole).not.toHaveBeenCalled()
  })

  it("cancel button closes create form", () => {
    renderView()
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))
    expect(screen.getByRole("heading", { name: "دور جديد" })).toBeInTheDocument()
    fireEvent.click(screen.getByText("إلغاء"))
    expect(screen.queryByPlaceholderText("اسم الدور")).not.toBeInTheDocument()
  })

  it("opens edit form with pre-filled data when edit clicked", () => {
    renderView()
    fireEvent.click(screen.getByLabelText("تعديل مدير المبيعات"))
    expect(screen.getByText("تعديل الدور")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("اسم الدور")).toHaveValue("مدير المبيعات")
    expect(screen.getByPlaceholderText("وصف (اختياري)")).toHaveValue("صلاحيات مدير فريق المبيعات")
  })

  it("calls onUpdateRole when saving edited role", () => {
    const onUpdateRole = jest.fn()
    renderView({ onUpdateRole })
    fireEvent.click(screen.getByLabelText("تعديل مدير المبيعات"))
    fireEvent.change(screen.getByPlaceholderText("اسم الدور"), { target: { value: "مدير مبيعات جديد" } })
    fireEvent.click(screen.getByText("حفظ"))
    expect(onUpdateRole).toHaveBeenCalledWith("role-1", expect.objectContaining({ name: "مدير مبيعات جديد" }))
  })

  it("shows permission groups with labels", () => {
    renderView()
    fireEvent.click(screen.getByRole("button", { name: /دور جديد/ }))
    expect(screen.getByText("الشركات")).toBeInTheDocument()
    expect(screen.getByText("جهات الاتصال")).toBeInTheDocument()
    expect(screen.getByText("الصفقات")).toBeInTheDocument()
  })

  it("shows 'no permissions' text when role has empty permissions", () => {
    const roleNoPerms: RoleItem = { ...sampleRole, permissions: [] }
    renderView({ roles: [roleNoPerms] })
    expect(screen.getByText("لا توجد صلاحيات")).toBeInTheDocument()
  })

  it("shows overflow count when role has more than 8 permissions", () => {
    const roleManyPerms: RoleItem = {
      ...sampleRole,
      permissions: ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
    }
    renderView({ roles: [roleManyPerms] })
    expect(screen.getByText("+2")).toBeInTheDocument()
  })
})
