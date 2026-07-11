"use client"

import { BarChart3 } from "lucide-react"
import { EmptyState } from "./EmptyState"

export function EmptyAnalytics() {
  return (
    <EmptyState
      icon={<BarChart3 className="h-12 w-12" />}
      title="بيانات غير كافية للتقارير"
      description="استمر في استخدام SalesOS لإضافة الصفقات، الشركات، وجهات الاتصال. كلما زادت بياناتك، زادت دقة التقارير والتحليلات."
      tourId="pipeline"
    />
  )
}
