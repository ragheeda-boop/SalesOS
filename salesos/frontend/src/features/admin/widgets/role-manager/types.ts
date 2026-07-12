export interface RoleManagerViewProps {
  roles: RoleItem[]
  permissions: PermissionItem[]
  loading: boolean
  onRefresh: () => void
  onCreateRole: (data: { name: string; description?: string; permissions: string[] }) => void
  onUpdateRole: (id: string, data: { name?: string; description?: string; permissions?: string[] }) => void
  onDeleteRole: (id: string) => void
}

export interface RoleItem {
  id: string
  name: string
  description: string | null
  permissions: string[]
  is_system: boolean
  user_count: number
}

export interface PermissionItem {
  id: string
  key: string
  name: string
  description: string | null
  group: string
}

export const PERMISSION_GROUP_LABELS: Record<string, string> = {
  users: "المستخدمين",
  tenants: "العملاء",
  roles: "الأدوار",
  billing: "الفواتير",
  ai: "الذكاء الاصطناعي",
  jobs: "الوظائف",
  features: "الميزات",
  settings: "الإعدادات",
  audit: "التدقيق",
  companies: "الشركات",
  contacts: "جهات الاتصال",
  deals: "الصفقات",
}
