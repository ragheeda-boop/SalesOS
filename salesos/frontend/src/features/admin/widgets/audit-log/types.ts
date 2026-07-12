import type { AuditLogEntry } from "@/lib/api"

export interface AuditLogViewProps {
  items: AuditLogEntry[]
  total: number
  loading: boolean
  filters: AuditLogFilters
  onFilterChange: (filters: Partial<AuditLogFilters>) => void
  onExport: () => void
  onRefresh: () => void
}

export interface AuditLogFilters {
  dateFrom?: string
  dateTo?: string
  userId?: string
  actionType?: string
  resource?: string
  search?: string
  page: number
  pageSize: number
}

export const ACTION_TYPE_LABELS: Record<string, string> = {
  create: "إنشاء",
  update: "تحديث",
  delete: "حذف",
  read: "قراءة",
  login: "تسجيل دخول",
  logout: "تسجيل خروج",
  export: "تصدير",
  import: "استيراد",
  assign: "تعيين",
  revoke: "إلغاء",
}

export const RESOURCE_LABELS: Record<string, string> = {
  user: "مستخدم",
  tenant: "عميل",
  role: "دور",
  permission: "صلاحية",
  company: "شركة",
  contact: "جهة اتصال",
  deal: "صفقة",
  plan: "باقة",
  license: "ترخيص",
  feature_flag: "ميزة",
  job: "وظيفة",
  settings: "إعدادات",
}
