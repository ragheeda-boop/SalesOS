'use client'

import { createWidget, createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { EmployeeProfile } from '@/lib/api'
import { User, Mail, Phone, Users, Shield, Calendar } from 'lucide-react'

export function EmployeeProfileView({ profile }: { profile: EmployeeProfile }) {
  const initials = profile.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
  const createdDate = new Date(profile.created_at).toLocaleDateString('ar-SA')

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[var(--muhide-orange)] to-[var(--muhide-brown)] flex items-center justify-center text-white font-bold shrink-0">
          {profile.avatar_url ? (
            <img src={profile.avatar_url} alt={profile.full_name} className="w-full h-full rounded-full object-cover" />
          ) : initials}
        </div>
        <div>
          <p className="font-semibold text-[var(--text-primary)]">{profile.full_name_ar || profile.full_name}</p>
          <p className="text-xs text-[var(--text-secondary)]">{profile.role}</p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
          <Mail className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          <span dir="ltr">{profile.email}</span>
        </div>
        {profile.phone && (
          <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
            <Phone className="h-3.5 w-3.5 text-[var(--text-muted)]" />
            <span dir="ltr">{profile.phone}</span>
          </div>
        )}
        <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
          <Calendar className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          <span>منذ {createdDate}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
          <Shield className={profile.is_active ? 'text-success-500 h-3.5 w-3.5' : 'text-[var(--text-muted)] h-3.5 w-3.5'} />
          <span>{profile.is_active ? 'نشط' : 'غير نشط'}</span>
        </div>
      </div>

      {profile.team.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2 flex items-center gap-1">
            <Users className="h-3 w-3" /> فريق العمل ({profile.team.length})
          </p>
          <div className="space-y-1.5">
            {profile.team.slice(0, 5).map((member: Record<string, unknown>) => (
              <div key={member.id as string} className="flex items-center gap-2 text-xs">
                <div className="w-5 h-5 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center text-[9px] font-medium text-[var(--text-muted)]">
                  {(member.full_name as string)?.charAt(0) || '?'}
                </div>
                <span className="text-[var(--text-secondary)]">{member.full_name as string}</span>
                <span className="text-[var(--text-muted)] mr-auto">{member.role as string}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!profile.team.length && !profile.manager && (
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <User className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-1" />
          <p className="text-xs text-[var(--text-muted)]">لا توجد معلومات إضافية</p>
        </div>
      )}
    </div>
  )
}

export const EmployeeProfileWidget = createWorkspaceWidget(
  { id: 'employeeProfile', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.profile,
  {
    metadata: { title: 'الملف الشخصي' },
    render: ({ data }) => <EmployeeProfileView profile={data} />,
  },
)
