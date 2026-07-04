export type AIAction = 'explain' | 'analyze' | 'improve' | 'predict' | 'summarize' | 'generate' | 'compare' | 'recommend'

export type ConfidenceLevel = 'low' | 'medium' | 'high' | 'very-high'

export interface AIActionDescriptor {
  id: AIAction
  icon: string
  labelAr: string
  labelEn: string
  descriptionAr: string
  descriptionEn: string
  requiresContext: boolean
  confidence?: ConfidenceLevel
}

export const AI_ACTIONS: Record<AIAction, AIActionDescriptor> = {
  explain: {
    id: 'explain',
    icon: 'HelpCircle',
    labelAr: 'شرح',
    labelEn: 'Explain',
    descriptionAr: 'شرح هذا العنصر بالتفصيل',
    descriptionEn: 'Explain this item in detail',
    requiresContext: true,
  },
  analyze: {
    id: 'analyze',
    icon: 'BarChart3',
    labelAr: 'تحليل',
    labelEn: 'Analyze',
    descriptionAr: 'تحليل البيانات واكتشاف الأنماط',
    descriptionEn: 'Analyze data and discover patterns',
    requiresContext: true,
  },
  improve: {
    id: 'improve',
    icon: 'TrendingUp',
    labelAr: 'تحسين',
    labelEn: 'Improve',
    descriptionAr: 'اقتراح طرق للتحسين',
    descriptionEn: 'Suggest ways to improve',
    requiresContext: true,
  },
  predict: {
    id: 'predict',
    icon: 'Zap',
    labelAr: 'توقع',
    labelEn: 'Predict',
    descriptionAr: 'توقع النتائج والاتجاهات المستقبلية',
    descriptionEn: 'Predict future outcomes and trends',
    requiresContext: true,
  },
  summarize: {
    id: 'summarize',
    icon: 'FileText',
    labelAr: 'تلخيص',
    labelEn: 'Summarize',
    descriptionAr: 'تلخيص المعلومات في نقاط رئيسية',
    descriptionEn: 'Summarize into key points',
    requiresContext: true,
  },
  generate: {
    id: 'generate',
    icon: 'Sparkles',
    labelAr: 'توليد',
    labelEn: 'Generate',
    descriptionAr: 'توليد محتوى جديد بناءً على السياق',
    descriptionEn: 'Generate new content based on context',
    requiresContext: true,
  },
  compare: {
    id: 'compare',
    icon: 'ArrowUpDown',
    labelAr: 'مقارنة',
    labelEn: 'Compare',
    descriptionAr: 'مقارنة هذا العنصر مع عناصر مشابهة',
    descriptionEn: 'Compare this item with similar ones',
    requiresContext: true,
  },
  recommend: {
    id: 'recommend',
    icon: 'ThumbsUp',
    labelAr: 'توصية',
    labelEn: 'Recommend',
    descriptionAr: 'الحصول على توصيات مخصصة',
    descriptionEn: 'Get personalized recommendations',
    requiresContext: true,
  },
}

export const AI_CONFIDENCE = {
  low: { label: 'منخفض', color: 'text-red-600', bg: 'bg-red-50', icon: 'AlertCircle' },
  medium: { label: 'متوسط', color: 'text-amber-600', bg: 'bg-amber-50', icon: 'HelpCircle' },
  high: { label: 'عال', color: 'text-green-600', bg: 'bg-green-50', icon: 'CheckCircle' },
  'very-high': { label: 'عال جداً', color: 'text-emerald-600', bg: 'bg-emerald-50', icon: 'CheckCircle2' },
} as const

export const AI_PATTERNS = {
  inline: { position: 'inline', iconSize: 14, variant: 'ghost' } as const,
  widget: { position: 'widget-header', iconSize: 16, variant: 'ghost' } as const,
  floating: { position: 'floating', iconSize: 18, variant: 'primary' } as const,
  toolbar: { position: 'toolbar', iconSize: 16, variant: 'secondary' } as const,
  selection: { position: 'selection', iconSize: 14, variant: 'ghost' } as const,
} as const

export interface AIResponse {
  content: string
  confidence: ConfidenceLevel
  sources?: string[]
  actions?: AIAction[]
  followUp?: string[]
  generatedAt: number
}
