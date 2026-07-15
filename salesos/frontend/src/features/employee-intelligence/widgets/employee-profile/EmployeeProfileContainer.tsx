'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { EmployeeProfile } from '@/lib/api'
import { useParams } from 'next/navigation'
import { EmployeeProfileView } from './EmployeeProfileView'

export function EmployeeProfileContainer({ employeeId }: { employeeId?: string }) {
  const params = useParams<{ id: string }>()
  const id = employeeId ?? params.id
  const { data, isLoading, error } = useQuery<EmployeeProfile>({
    queryKey: ['employee-profile', id],
    queryFn: () => api.get(`/employees/${id}/profile`).then((r: { data: EmployeeProfile }) => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-full bg-[var(--bg-secondary)]" />
          <div className="space-y-1.5">
            <div className="h-4 w-32 bg-[var(--bg-secondary)] rounded" />
            <div className="h-3 w-24 bg-[var(--bg-secondary)] rounded" />
          </div>
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map(i => <div key={i} className="h-4 w-full bg-[var(--bg-secondary)] rounded" />)}
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="text-xs text-[var(--color-danger-600)] p-3 bg-[var(--color-danger-50)] rounded-lg">خطأ في تحميل الملف الشخصي</div>
  }

  if (!data) {
    return <div className="text-xs text-[var(--text-muted)] p-3 text-center">لا توجد بيانات</div>
  }

  return <EmployeeProfileView profile={data} />
}
