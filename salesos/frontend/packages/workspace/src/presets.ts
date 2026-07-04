export type WorkspaceRole = 'sales' | 'marketing' | 'executive' | 'legal' | 'operations' | 'customer-success'

export interface WidgetPreset {
  id: string
  span: 1 | 2 | 3 | 4 | 6 | 12
  order: number
  size?: 'small' | 'medium' | 'large'
}

export interface PresetAction {
  id: string
  label: string
  icon?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'danger'
}

export interface WorkspacePreset {
  id: WorkspaceRole
  labelAr: string
  labelEn: string
  description: string
  metricWidgets: string[]
  primaryWidgets: string[]
  metricsColumns: number
  availableWidgets: string[]
  defaultWidgets: WidgetPreset[]
  actions?: PresetAction[]
  density: import('@salesos/design-language').Density
}

export const WORKSPACE_PRESETS: Record<WorkspaceRole, WorkspacePreset> = {
  sales: {
    id: 'sales',
    labelAr: 'مبيعات',
    labelEn: 'Sales',
    description: 'مساحة عمل فريق المبيعات مع التركيز على الصفقات والإيرادات',
    metricWidgets: ['revenue', 'deals', 'meetings', 'signals'],
    primaryWidgets: ['buying-committee', 'timeline'],
    metricsColumns: 4,
    availableWidgets: ['revenue', 'deals', 'meetings', 'signals', 'buying-committee', 'timeline', 'ai-recommendations', 'forecast', 'tasks', 'contacts'],
    defaultWidgets: [
      { id: 'revenue', span: 3, order: 0, size: 'medium' },
      { id: 'forecast', span: 3, order: 1, size: 'medium' },
      { id: 'buying-committee', span: 4, order: 2, size: 'large' },
      { id: 'timeline', span: 4, order: 3, size: 'large' },
      { id: 'signals', span: 4, order: 4, size: 'medium' },
      { id: 'ai-recommendations', span: 4, order: 5, size: 'medium' },
      { id: 'tasks', span: 2, order: 6, size: 'small' },
      { id: 'contacts', span: 2, order: 7, size: 'small' },
    ],
    actions: [
      { id: 'create-deal', label: 'صفقة جديدة', icon: 'Plus', variant: 'primary' },
      { id: 'log-meeting', label: 'تسجيل اجتماع', icon: 'Calendar' },
    ],
    density: 'normal',
  },
  marketing: {
    id: 'marketing',
    labelAr: 'تسويق',
    labelEn: 'Marketing',
    description: 'مساحة عمل فريق التسويق مع التركيز على الحملات والجماهير',
    metricWidgets: ['campaigns', 'engagement', 'leads', 'conversion'],
    primaryWidgets: ['campaign-performance', 'audience'],
    metricsColumns: 4,
    availableWidgets: ['campaigns', 'engagement', 'leads', 'conversion', 'campaign-performance', 'audience', 'ai-insights', 'content', 'sequences', 'analytics'],
    defaultWidgets: [
      { id: 'campaign-performance', span: 6, order: 0, size: 'large' },
      { id: 'audience', span: 6, order: 1, size: 'large' },
      { id: 'ai-insights', span: 4, order: 2, size: 'medium' },
      { id: 'sequences', span: 4, order: 3, size: 'medium' },
      { id: 'content', span: 4, order: 4, size: 'medium' },
    ],
    actions: [
      { id: 'create-campaign', label: 'حملة جديدة', icon: 'Plus', variant: 'primary' },
      { id: 'import-audience', label: 'استيراد جمهور', icon: 'Upload' },
    ],
    density: 'normal',
  },
  executive: {
    id: 'executive',
    labelAr: 'تنفيذي',
    labelEn: 'Executive',
    description: 'لوحة القيادة التنفيذية مع التركيز على المؤشرات الاستراتيجية',
    metricWidgets: ['revenue', 'growth', 'pipeline', 'churn'],
    primaryWidgets: ['forecast', 'revenue-brain'],
    metricsColumns: 4,
    availableWidgets: ['revenue', 'growth', 'pipeline', 'churn', 'forecast', 'revenue-brain', 'ai-executive-summary', 'decisions', 'top-accounts', 'market-trends'],
    defaultWidgets: [
      { id: 'revenue-brain', span: 6, order: 0, size: 'large' },
      { id: 'forecast', span: 6, order: 1, size: 'large' },
      { id: 'ai-executive-summary', span: 6, order: 2, size: 'large' },
      { id: 'decisions', span: 6, order: 3, size: 'large' },
      { id: 'top-accounts', span: 4, order: 4, size: 'medium' },
      { id: 'market-trends', span: 4, order: 5, size: 'medium' },
    ],
    density: 'comfortable',
  },
  legal: {
    id: 'legal',
    labelAr: 'قانوني',
    labelEn: 'Legal',
    description: 'مساحة عمل الفريق القانوني مع التركيز على التراخيص والامتثال',
    metricWidgets: ['licenses', 'compliance', 'contracts', 'risks'],
    primaryWidgets: ['licenses-list', 'contracts'],
    metricsColumns: 4,
    availableWidgets: ['licenses', 'compliance', 'contracts', 'risks', 'licenses-list', 'contracts-list', 'audit-log', 'ai-legal-summary', 'documents', 'obligations'],
    defaultWidgets: [
      { id: 'licenses-list', span: 6, order: 0, size: 'large' },
      { id: 'contracts-list', span: 6, order: 1, size: 'large' },
      { id: 'compliance', span: 4, order: 2, size: 'medium' },
      { id: 'risks', span: 4, order: 3, size: 'medium' },
      { id: 'audit-log', span: 4, order: 4, size: 'medium' },
    ],
    density: 'compact',
  },
  operations: {
    id: 'operations',
    labelAr: 'عمليات',
    labelEn: 'Operations',
    description: 'مساحة عمل فريق العمليات مع التركيز على البيانات والتكامل',
    metricWidgets: ['data-health', 'integrations', 'errors', 'uptime'],
    primaryWidgets: ['data-quality', 'integrations-list'],
    metricsColumns: 4,
    availableWidgets: ['data-health', 'integrations', 'errors', 'uptime', 'data-quality', 'integrations-list', 'audit-log', 'ai-summary', 'jobs', 'settings'],
    defaultWidgets: [
      { id: 'data-quality', span: 6, order: 0, size: 'large' },
      { id: 'integrations-list', span: 6, order: 1, size: 'large' },
      { id: 'audit-log', span: 6, order: 2, size: 'large' },
      { id: 'jobs', span: 4, order: 3, size: 'medium' },
    ],
    density: 'compact',
  },
  'customer-success': {
    id: 'customer-success',
    labelAr: 'نجاح العملاء',
    labelEn: 'Customer Success',
    description: 'مساحة عمل فريق نجاح العملاء مع التركيز على صحة العملاء والتجديدات',
    metricWidgets: ['health-score', 'usage', 'renewals', 'satisfaction'],
    primaryWidgets: ['health-trend', 'renewals-list'],
    metricsColumns: 4,
    availableWidgets: ['health-score', 'usage', 'renewals', 'satisfaction', 'health-trend', 'renewals-list', 'ai-insights', 'success-plans', 'tasks', 'communications'],
    defaultWidgets: [
      { id: 'health-trend', span: 6, order: 0, size: 'large' },
      { id: 'renewals-list', span: 6, order: 1, size: 'large' },
      { id: 'ai-insights', span: 4, order: 2, size: 'medium' },
      { id: 'success-plans', span: 4, order: 3, size: 'medium' },
      { id: 'tasks', span: 4, order: 4, size: 'medium' },
    ],
    density: 'normal',
  },
}

export function getPreset(role: WorkspaceRole): WorkspacePreset {
  return WORKSPACE_PRESETS[role]
}

export function getAllPresets(): WorkspacePreset[] {
  return Object.values(WORKSPACE_PRESETS)
}
