'use client'

import { createWidget } from '@salesos/workspace'
import type { MeetingBrief } from '@/application/revenue-execution/meeting.dto'
import { MeetingView } from './MeetingView'

const sampleBrief: MeetingBrief = {
  companyName: 'شركة الطاقة', meetingTitle: 'اجتماع المتابعة الربعي', date: '2026-07-15',
  attendees: [{ name: 'د. أحمد السلمي', role: 'CEO', influence: 'عالي' }, { name: 'نورة القحطاني', role: 'CTO', influence: 'متوسط' }],
  recentSignals: ['إعلان توسع في الرياض', 'توظيف 50 مهندس', 'شراكة استراتيجية مع STC'],
  risks: ['مورد بديل قيد التقييم'],
  opportunities: ['فرصة لعقد طويل الأمد بقيمة 2 مليون'],
  talkingPoints: ['عرض أحدث الحلول في الطاقة المتجددة', 'مناقشة الاحتياجات الحالية', 'تقديم دراسة حالة لشركة مماثلة'],
  recommendedAction: 'تقديم عرض توضيحي خلال أسبوع',
}

export const MeetingIntelligenceWidget = createWidget({
  metadata: {
    id: 'meetingIntelligence', title: 'ذكاء الاجتماعات', category: 'intelligence', priority: 'high',
    permissions: ['meeting:read'], featureFlag: { enabled: true }, minHeight: '360px',
  },
  useData: () => ({ data: sampleBrief, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <MeetingView brief={data} />,
})
