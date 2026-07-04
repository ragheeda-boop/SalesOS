export interface EmptyStateConfig {
  icon: string
  title: string
  description: string
  action: {
    label: string
    handler: string
  }
  secondaryAction?: {
    label: string
    handler: string
  }
  illustration?: string
}

export const EMPTY_STATES: Record<string, EmptyStateConfig> = {
  noCompanies: {
    icon: 'Building2',
    title: 'لا توجد شركات بعد',
    description: 'قم باستيراد بيانات الشركات للبدء في تحليل الحسابات واكتشاف الفرص.',
    action: { label: 'استيراد شركات', handler: 'import.companies' },
    secondaryAction: { label: 'معرفة المزيد', handler: 'docs.companies' },
  },
  noDeals: {
    icon: 'DollarSign',
    title: 'لا توجد صفقات',
    description: 'أنشئ أول صفقة لك لتتبع فرص البيع وإدارة دورة المبيعات.',
    action: { label: 'إنشاء صفقة', handler: 'create.deal' },
  },
  noContacts: {
    icon: 'Users',
    title: 'لا توجد جهات اتصال',
    description: 'جهات الاتصال تساعدك في بناء العلاقات وإدارة التواصل مع العملاء.',
    action: { label: 'إضافة جهة اتصال', handler: 'create.contact' },
    secondaryAction: { label: 'استيراد جهات اتصال', handler: 'import.contacts' },
  },
  noActivities: {
    icon: 'Activity',
    title: 'لا توجد نشاطات حديثة',
    description: 'النشاطات تظهر هنا عندما تبدأ التفاعل مع العملاء.',
    action: { label: 'تسجيل نشاط', handler: 'create.activity' },
  },
  noResults: {
    icon: 'Search',
    title: 'لا توجد نتائج',
    description: 'حاول تغيير معايير البحث أو استخدام كلمات مفتاحية مختلفة.',
    action: { label: 'مسح البحث', handler: 'search.clear' },
  },
  noNotifications: {
    icon: 'Bell',
    title: 'لا توجد إشعارات',
    description: 'الإشعارات الجديدة ستظهر هنا عندما تكون هناك تحديثات مهمة.',
    action: { label: 'عرض الإعدادات', handler: 'settings.notifications' },
  },
  noTimeline: {
    icon: 'Clock',
    title: 'لا توجد أحداث في الجدول الزمني',
    description: 'الأحداث تظهر هنا عند حدوث تغييرات أو تفاعلات مهمة.',
    action: { label: 'مشاهدة التغييرات', handler: 'timeline.all' },
  },
  noSignals: {
    icon: 'Zap',
    title: 'لا توجد إشارات',
    description: 'سيتم اكتشاف الإشارات تلقائياً عند توفر بيانات كافية.',
    action: { label: 'تهيئة المصادر', handler: 'settings.signals' },
  },
} as const

export const LOADING_STATES = {
  initial: {
    label: 'جاري التحميل...',
    description: 'يتم تحضير البيانات لعرضها',
    icon: 'Loader2',
  },
  refreshing: {
    label: 'جاري التحديث...',
    description: 'يتم تحديث البيانات من المصادر',
    icon: 'RefreshCw',
  },
  searching: {
    label: 'جاري البحث...',
    description: 'يتم البحث في البيانات المتاحة',
    icon: 'Search',
  },
  analyzing: {
    label: 'جاري التحليل...',
    description: 'AI يقوم بتحليل البيانات',
    icon: 'Sparkles',
  },
  syncing: {
    label: 'جاري المزامنة...',
    description: 'يتم مزامنة البيانات مع الخادم',
    icon: 'UploadCloud',
  },
} as const

export const ERROR_STATES = {
  generic: {
    title: 'حدث خطأ',
    description: 'تعذر تحميل البيانات. حاول مرة أخرى.',
    action: 'إعادة المحاولة',
  },
  network: {
    title: 'لا يوجد اتصال',
    description: 'تحقق من اتصالك بالإنترنت وحاول مرة أخرى.',
    action: 'إعادة المحاولة',
  },
  notFound: {
    title: 'غير موجود',
    description: 'لم يتم العثور على العنصر المطلوب.',
    action: 'العودة',
  },
  forbidden: {
    title: 'لا توجد صلاحية',
    description: 'ليس لديك صلاحية الوصول إلى هذا المحتوى.',
    action: 'طلب صلاحية',
  },
  timeout: {
    title: 'انتهت المهلة',
    description: 'استغرقت العملية وقتاً أطول من المتوقع.',
    action: 'إعادة المحاولة',
  },
  serverError: {
    title: 'خطأ في الخادم',
    description: 'حدث خطأ داخلي. الفريق الفني على علم بالمشكلة.',
    action: 'المتابعة',
  },
} as const
