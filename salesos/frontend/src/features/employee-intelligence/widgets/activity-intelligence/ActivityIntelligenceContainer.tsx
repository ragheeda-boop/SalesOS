'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { ActivityIntelligence } from '@/lib/api'
import { useParams } from 'next/navigation'
import { ActivityIntelligenceView } from './ActivityIntelligenceView'

export function ActivityIntelligenceContainer({ entityId }: { entityId?: string }) {
  const params = useParams<{ id: string }>()
  const id = entityId ?? params.id
  const { data, isLoading, error } = useQuery<ActivityIntelligence>({
    queryKey: ['activity-intelligence', id],
    queryFn: () => api.get(`/employees/${id}/activity-intelligence`).then((r: { data: ActivityIntelligence }) => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="grid grid-cols-4 gap-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-lg p-2 bg-[var(--bg-secondary)]">
              <div className="h-7 w-7 rounded-lg bg-[var(--bg-tertiary)] mx-auto mb-1" />
              <div className="h-4 w-6 mx-auto bg-[var(--bg-tertiary)] rounded" />
              <div className="h-2.5 w-8 mx-auto mt-1 bg-[var(--bg-tertiary)] rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="text-xs text-[var(--color-danger-600)] p-3 bg-[var(--color-danger-50)] rounded-lg">خطأ في تحميل بيانات النشاط</div>
  }

  if (!data) {
    return <div className="text-xs text-[var(--text-muted)] p-3 text-center">لا توجد بيانات نشاط</div>
  }

  return <ActivityIntelligenceView data={data} />
}
