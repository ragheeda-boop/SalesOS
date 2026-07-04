export const FOCUS = {
  ring: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500',
  ringOffset: 2,
  ringWidth: 2,
  ringColor: 'rgb(59, 130, 246)',
  transition: 'transition-colors duration-100',
}

export const KEYBOARD = {
  shortcuts: {
    search: { key: 'k', meta: true, labelAr: 'بحث سريع', labelEn: 'Quick search' },
    command: { key: 'k', meta: true, shift: true, labelAr: 'الأوامر', labelEn: 'Commands' },
    copilot: { key: 'i', meta: true, labelAr: 'المساعد الذكي', labelEn: 'AI Copilot' },
    navigate: { key: 'g', meta: true, labelAr: 'التنقل السريع', labelEn: 'Quick navigate' },
    theme: { key: 't', meta: true, labelAr: 'تبديل السمة', labelEn: 'Toggle theme' },
    notifications: { key: 'n', meta: true, labelAr: 'الإشعارات', labelEn: 'Notifications' },
    help: { key: '/', meta: true, labelAr: 'المساعدة', labelEn: 'Help' },
    create: { key: 'c', meta: true, shift: true, labelAr: 'إنشاء', labelEn: 'Create' },
    save: { key: 's', meta: true, labelAr: 'حفظ', labelEn: 'Save' },
    close: { key: 'Escape', labelAr: 'إغلاق', labelEn: 'Close' },
  },
  navigation: {
    nextItem: { key: 'ArrowDown', labelAr: 'العنصر التالي', labelEn: 'Next item' },
    prevItem: { key: 'ArrowUp', labelAr: 'العنصر السابق', labelEn: 'Previous item' },
    selectItem: { key: 'Enter', labelAr: 'اختيار', labelEn: 'Select' },
    expandSection: { key: 'ArrowRight', labelAr: 'توسيع', labelEn: 'Expand' },
    collapseSection: { key: 'ArrowLeft', labelAr: 'طي', labelEn: 'Collapse' },
  },
} as const

export const SCREEN_READER = {
  liveRegion: 'aria-live="polite" aria-atomic="true"',
  srOnly: 'sr-only',
  announcements: {
    pageLoaded: (name: string) => `تم تحميل ${name}`,
    dataLoaded: (count: number) => `تم تحميل ${count} عنصر`,
    actionComplete: (action: string) => `تم ${action} بنجاح`,
    error: (msg: string) => `خطأ: ${msg}`,
    loading: (name: string) => `جاري تحميل ${name}`,
    aiResponse: (action: string) => `AI قام ب ${action}`,
  },
}

export interface ARIALabel {
  label: string
  description?: string
  role?: string
}

export const ARIAS = {
  commandBar: { label: 'شريط الأوامر', description: 'ابحث عن الأوامر والوظائف', role: 'dialog' },
  searchPanel: { label: 'البحث العام', description: 'ابحث في الشركات وجهات الاتصال والفرص', role: 'search' },
  copilotPanel: { label: 'المساعد الذكي', description: 'اسأل المساعد الذكي عن أي شيء', role: 'dialog' },
  workspace: { label: 'مساحة العمل', role: 'main' },
  sidebar: { label: 'القائمة الجانبية', role: 'navigation' },
  timeline: { label: 'الجدول الزمني', role: 'feed' },
  inbox: { label: 'صندوق الوارد', description: 'المهام والإشعارات والتوصيات', role: 'list' },
  notifications: { label: 'الإشعارات', role: 'log' },
  widget: (name: string): ARIALabel => ({ label: `عنصر ${name}`, role: 'region' }),
  card: (name: string): ARIALabel => ({ label: `بطاقة ${name}`, role: 'article' }),
  table: (name: string): ARIALabel => ({ label: `جدول ${name}`, role: 'table' }),
} as const
