export interface SearchDesign {
  shortcut: string
  placeholder: string
  maxResults: number
  debounceMs: number
  sections: {
    label: string
    icon: string
    priority: number
  }[]
  filters: {
    type: string
    label: string
    icon: string
  }[]
}

export const SEARCH_DESIGN = {
  shortcut: '⌘K',
  placeholder: 'ابحث في أي شيء...',
  maxResults: 50,
  debounceMs: 300,
  sections: [
    { label: 'الشركات', icon: 'Building2', priority: 1 },
    { label: 'جهات الاتصال', icon: 'Users', priority: 2 },
    { label: 'الصفقات', icon: 'DollarSign', priority: 3 },
    { label: 'المستندات', icon: 'FileText', priority: 4 },
    { label: 'النشاطات', icon: 'Activity', priority: 5 },
  ],
  filters: [
    { type: 'all', label: 'الكل', icon: 'Search' },
    { type: 'company', label: 'الشركات', icon: 'Building2' },
    { type: 'contact', label: 'جهات الاتصال', icon: 'Users' },
    { type: 'deal', label: 'الصفقات', icon: 'DollarSign' },
    { type: 'document', label: 'المستندات', icon: 'FileText' },
  ],
} as const

export interface CommandPaletteDesign {
  shortcut: string
  placeholder: string
  groups: {
    label: string
    icon: string
    commands: string[]
  }[]
  recentCount: number
  maxDisplay: number
}

export const COMMAND_DESIGN = {
  shortcut: '⌘P',
  placeholder: 'اكتب أمر أو ابحث...',
  groups: [
    { label: 'تنقل', icon: 'Navigation', commands: ['go.dashboard', 'go.companies', 'go.deals', 'go.contacts', 'go.settings'] },
    { label: 'إجراءات', icon: 'Zap', commands: ['action.create', 'action.import', 'action.export', 'action.copilot', 'action.search'] },
    { label: 'AI', icon: 'Sparkles', commands: ['ai.analyze', 'ai.summarize', 'ai.generate', 'ai.recommend', 'ai.translate'] },
    { label: 'عرض', icon: 'Eye', commands: ['view.toggle-sidebar', 'view.toggle-timeline', 'view.zoom-in', 'view.zoom-out', 'view.theme'] },
  ],
  recentCount: 5,
  maxDisplay: 20,
} as const
