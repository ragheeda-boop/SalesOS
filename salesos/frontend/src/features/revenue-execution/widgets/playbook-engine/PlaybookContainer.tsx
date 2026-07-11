'use client'

import { createWidget } from '@salesos/workspace'
import type { Playbook } from '@/application/revenue-execution/playbook.dto'
import { PlaybookView } from './PlaybookView'

const PLAYBOOKS: Record<string, Playbook> = {
  energy: { id: 'pb-energy', name: 'دليل الطاقة', description: 'استراتيجية اختراق قطاع الطاقة مع التركيز على العقود الطويلة', industry: 'energy', estimatedDuration: '8-12 أسبوع', successRate: 72, steps: [
    { id: 'e1', order: 1, title: 'تحديد صانعي القرار', description: 'تحديد رئيس قسم المشتريات وكبار المهندسين', duration: 'أسبوع' },
    { id: 'e2', order: 2, title: 'عرض القيمة للطاقة', description: 'تقديم حلول مخصصة لخفض التكاليف وزيادة الكفاءة', duration: 'أسبوعين' },
    { id: 'e3', order: 3, title: 'جولة تعريفية', description: 'تنظيم جولة في منشآت العميل مع خبراء تقنيين', duration: 'أسبوع' },
    { id: 'e4', order: 4, title: 'عرض تجريبي', description: 'عرض توضيحي للمنتج مع حالات استخدام فعلية', duration: 'أسبوع' },
    { id: 'e5', order: 5, title: 'تفاوض وإغلاق', description: 'تقديم عرض سعر والتفاوض على الشروط', duration: '2-4 أسابيع' },
  ]},
  healthcare: { id: 'pb-health', name: 'دليل الرعاية الصحية', description: 'استراتيجية اختراق قطاع الرعاية الصحية مع التركيز على الامتثال', industry: 'healthcare', estimatedDuration: '10-14 أسبوع', successRate: 68, steps: [
    { id: 'h1', order: 1, title: 'التحقق من الامتثال', description: 'مراجعة متطلبات الهيئة السعودية للتخصصات الصحية', duration: 'أسبوع' },
    { id: 'h2', order: 2, title: 'التواصل مع المشتريات', description: 'التواصل مع إدارة المشتريات في المستشفيات', duration: 'أسبوعين' },
    { id: 'h3', order: 3, title: 'إثبات المفهوم', description: 'تقديم تجربة مجانية مع أحد المستشفيات', duration: '3 أسابيع' },
    { id: 'h4', order: 4, title: 'عرض النتائج', description: 'عرض نتائج إثبات المفهوم مع توصيات', duration: 'أسبوع' },
    { id: 'h5', order: 5, title: 'عقد طويل الأمد', description: 'تقديم عقد متعدد السنوات مع شروط مرنة', duration: '2-4 أسابيع' },
  ]},
}

function getPlaybook(industry: string): Playbook | null {
  return PLAYBOOKS[industry] ?? null
}

export const PlaybookWidget = createWidget({
  metadata: {
    id: 'playbookEngine', title: 'محرك اللعب', category: 'intelligence', priority: 'high',
    permissions: ['playbook:read'], featureFlag: { enabled: true }, minHeight: '360px',
  },
  useData: () => ({ data: { playbook: getPlaybook('energy'), industry: 'energy' }, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <PlaybookView playbook={data.playbook} industry={data.industry} />,
})
