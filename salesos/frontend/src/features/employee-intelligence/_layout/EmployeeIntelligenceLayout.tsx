'use client'

import { cn } from '@salesos/ui'
import { useMy360 } from '@/lib/hooks/employeeQueries'
import type { Employee360Response } from '@/lib/api'
import { Building2, TrendingUp, Target, Users, Calendar, Activity } from 'lucide-react'

interface StatCard {
  label: string
  value: string
  icon: React.ReactNode
  color: string
}

function StatsCards({ data }: { data: Employee360Response }) {
  const { kpis, portfolio, calendar_intelligence } = data

  const stats: StatCard[] = [
    { label: 'الإيرادات', value: `${kpis.revenue.toLocaleString()}`, icon: <TrendingUp className="h-4 w-4" />, color: 'text-success-600 bg-success-50' },
    { label: 'خط التصفية', value: `${kpis.pipeline.toLocaleString()}`, icon: <Target className="h-4 w-4" />, color: 'text-info-600 bg-info-50' },
    { label: 'نسبة الفوز', value: `${Math.round(kpis.win_rate * 100)}%`, icon: <Activity className="h-4 w-4" />, color: 'text-warning-600 bg-warning-50' },
    { label: 'شركات', value: `${portfolio.companies.length}`, icon: <Building2 className="h-4 w-4" />, color: 'text-purple-600 bg-purple-50' },
    { label: 'جهات اتصال', value: `${portfolio.contacts.length}`, icon: <Users className="h-4 w-4" />, color: 'text-cyan-600 bg-cyan-50' },
    { label: 'اجتماعات هذا الشهر', value: `${calendar_intelligence.month_count}`, icon: <Calendar className="h-4 w-4" />, color: 'text-danger-600 bg-danger-50' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {stats.map((stat) => (
        <div key={stat.label} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('flex items-center justify-center w-7 h-7 rounded-lg', stat.color.split(' ')[1])}>
              <span className={stat.color.split(' ')[0]}>{stat.icon}</span>
            </span>
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{stat.value}</p>
          <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
        </div>
      ))}
    </div>
  )
}

function ProfileHeader({ data }: { data: Employee360Response }) {
  const { profile } = data
  const initials = profile.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()

  return (
    <div className="flex items-center gap-4">
      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[var(--muhide-orange)] to-[var(--muhide-brown)] flex items-center justify-center text-white font-bold text-lg shrink-0">
        {profile.avatar_url ? (
          <img src={profile.avatar_url} alt={profile.full_name} className="w-full h-full rounded-full object-cover" />
        ) : initials}
      </div>
      <div>
        <h1 className="text-xl font-display text-[var(--text-primary)]">{profile.full_name_ar || profile.full_name}</h1>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-sm text-[var(--text-secondary)]">{profile.role}</span>
          <span className="text-[var(--text-muted)]">·</span>
          <span className="text-sm text-[var(--text-muted)]">{profile.email}</span>
          {profile.manager && (
            <>
              <span className="text-[var(--text-muted)]">·</span>
              <span className="text-sm text-[var(--text-muted)]">المدير: {profile.manager.full_name as string || ''}</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export function EmployeeIntelligenceLayout({ children }: { children: React.ReactNode }) {
  const { data, isLoading, isError, error } = useMy360()

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-16 bg-neutral-100 rounded-xl" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 bg-neutral-100 rounded-xl" />
          ))}
        </div>
        <div className="h-96 bg-neutral-100 rounded-xl" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-medium text-[var(--status-error)]">تعذر تحميل بيانات الموظف</p>
        <p className="text-sm text-[var(--text-muted)] mt-1">{error?.message}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6" dir="rtl">
      <ProfileHeader data={data} />
      <StatsCards data={data} />
      {children}
    </div>
  )
}
