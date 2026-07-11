import { http, HttpResponse } from 'msw'

const now = new Date().toISOString()

const companies = [
  { id: 'comp_001', name_ar: 'أرامكو السعودية', name_en: 'Saudi Aramco', cr_number: '1010000001', city: 'الظهران', region: 'المنطقة الشرقية', status: 'نشط', industry: 'energy' },
  { id: 'comp_002', name_ar: 'STC', name_en: 'Saudi Telecom Company', cr_number: '1010000002', city: 'الرياض', region: 'منطقة الرياض', status: 'نشط', industry: 'telecom' },
  { id: 'comp_003', name_ar: 'الراجحي', name_en: 'Al Rajhi Bank', cr_number: '1010000003', city: 'الرياض', region: 'منطقة الرياض', status: 'نشط', industry: 'financial' },
]

export const handlers = [
  // ─── Dashboard ─────────────────────────────────────
  http.get('/api/v1/dashboard', () => {
    return HttpResponse.json({
      generatedAt: now,
      period: 'today',
      totalTracked: 127,
      missionCenter: { data: { mission: 'زيادة الإيرادات بنسبة 15% هذا الربع', progress: 62, keyResults: [{ label: 'الصفقات المغلقة', current: 18, target: 25 }, { label: 'الاجتماعات', current: 42, target: 60 }, { label: 'الإشارات الجديدة', current: 85, target: 100 }], updatedAt: now }, status: 'ready' },
      decisionQueue: { data: { decisions: [{ id: 'd1', title: 'متابعة شركة الطاقة', priority: 'high', impact: '500K', due: now, status: 'pending' }, { id: 'd2', title: 'تقديم عرض STC', priority: 'critical', impact: '1.2M', due: now, status: 'pending' }] }, status: 'ready' },
      intelligenceFeed: { data: { items: [{ id: 'i1', type: 'signal', title: 'إشارة توسع من أرامكو', summary: 'خطة توسعية في الطاقة المتجددة', severity: 'high', timestamp: now }, { id: 'i2', type: 'news', title: 'STC تعلن عن شراكة', summary: 'اتفاقية مع شركة تقنية', severity: 'medium', timestamp: now }] }, status: 'ready' },
      aiBrief: { data: { summary: 'تم تحديد 3 فرص استراتيجية جديدة هذا الأسبوع', highlights: ['شراكة محتملة مع بنك الرياض', 'ارتفاع مؤشر الثقة في قطاع الطاقة'], generatedAt: now }, status: 'ready' },
      marketPulse: { data: { topMovers: [{ name: 'قطاع الطاقة', change: 2.5 }, { name: 'قطاع التقنية', change: 1.8 }], trends: ['ارتفاع الطلب على الطاقة النظيفة', 'توسع الاستثمار في التقنية المالية'] }, status: 'ready' },
      recentActivity: { data: { items: [{ id: 'a1', type: 'meeting', title: 'اجتماع مع أرامكو', companyName: 'أرامكو', timestamp: now }, { id: 'a2', type: 'signal', title: 'إشارة توسع', companyName: 'STC', timestamp: now }], total: 2 }, status: 'ready' },
    })
  }),

  // ─── Company Intelligence ──────────────────────────
  http.get('/api/v1/companies/:id/intelligence', ({ params }) => {
    const company = companies.find((c) => c.id === params.id) ?? companies[0]
    const industry = company?.industry ?? 'energy'
    return HttpResponse.json({
      companyId: params.id,
      generatedAt: now,
      dna: {
        industry, businessModel: industry === 'energy' ? 'b2b' : 'b2c',
        size: { employees: 15000, revenue: '1.2B', label: 'enterprise' },
        growthPattern: 'accelerating',
        buyingBehaviour: { score: 78, intent: 'high' },
        technologyProfile: { erp: 'sap', crm: 'salesforce' },
        financialHealth: { score: 82, revenue: 1_200_000_000, growth: 12.5, trend: 'up' },
        governmentExposure: { level: 'high', contracts: 45 },
        expansionPotential: { score: 72, markets: ['UAE', 'Egypt'] },
        digitalPresence: { score: 68, website: 'active', social: 'active' },
        hiringTrend: { trend: 'growing', openings: 120 },
        procurementMaturity: { score: 65, level: 'managed' },
        relationshipStrength: { score: 70, connections: 15 },
        buyingIntent: { score: 82, confidence: 0.88 },
        riskLevel: { score: 25, level: 'low' },
        confidenceScore: 0.92,
        dataFreshness: { score: 90, updatedAt: now },
        goldenRecordStatus: { status: 'clean', sources: 5 },
      },
      aiRecommendation: {
        action: 'meeting', actionLabel: 'ترتيب اجتماع', reasoning: 'ارتفاع نية الشراء مع توفر جهات اتخاذ القرار',
        confidence: 0.85, expectedRevenue: 500000, expectedImpact: 'high', estimatedTime: 'أسبوعين',
        alternatives: [{ action: 'send_proposal', actionLabel: 'إرسال عرض', confidence: 0.7 }],
        risks: ['مورد بديل قيد التقييم'],
      },
      decisionMakers: [
        { id: 'dm1', name: 'د. أحمد السلمي', role: 'CEO', department: 'الإدارة العليا', influence: 'high', connected: true, email: 'a@salesos.com', lastInteraction: now },
        { id: 'dm2', name: 'نورة القحطاني', role: 'CTO', department: 'التقنية', influence: 'medium', connected: false },
      ],
      relationships: { nodes: [{ id: 'n1', type: 'person', label: 'د. أحمد', strength: 0.9 }, { id: 'n2', type: 'company', label: 'أرامكو', strength: 0.8 }], edges: [{ source: 'n1', target: 'n2', type: 'works_at', label: 'يعمل في', direction: 'outbound' }] },
      timeline: [{ id: 't1', type: 'signal', summary: 'إعلان توسع في المنطقة الشرقية', date: now, source: 'News', aiHighlighted: true, confidence: 0.92 }],
      signals: [{ id: 's1', type: 'hiring', title: 'توظيف 120 مهندس', description: 'خطة توسعية', source: 'LinkedIn', severity: 'high', timestamp: now, aiConfidence: 0.92 }],
      government: [{ id: 'g1', type: 'cr', title: 'السجل التجاري', status: 'active', source: 'وزارة التجارة', confidence: 0.95, freshness: now }],
      documents: [{ id: 'd1', title: 'عقد توريد 2026', type: 'contract', date: now, aiSummary: 'عقد توريد مواد بـ 2 مليون ريال', confidence: 0.92 }],
      buyingJourney: { currentStage: 'evaluation', progress: 45, timeInStage: '14 يوم', recommendedAction: 'تقديم عرض توضيحي', stageDescription: 'العميل يقيم الموردين المحتملين' },
      goldenRecord: [{ id: 'gr1', entityName: company?.name_ar ?? 'شركة', source: 'CRM', confidence: 0.98, conflicts: [], freshness: now, status: 'matched' }],
      firmographic: { nameAr: company?.name_ar ?? 'شركة', nameEn: company?.name_en ?? 'Company', crNumber: company?.cr_number ?? '', city: company?.city ?? '', region: company?.region ?? '', status: company?.status ?? '', industry, employees: 15000, foundedYear: 2000, businessModel: 'b2b' },
    })
  }),

  // ─── Search ────────────────────────────────────────
  http.post('/api/v1/search', async ({ request }) => {
    const body: any = await request.json()
    const results = Array.from({ length: 5 }, (_, i) => ({
      id: `result_${i + 1}`,
      entity_type: i === 0 ? 'company' : i === 1 ? 'person' : 'signal',
      title: i === 0 ? 'شركة أرامكو السعودية' : i === 1 ? 'د. أحمد السلمي' : `إشارة ${i + 1}`,
      subtitle: i === 0 ? 'شركة نفط وغاز وطنية' : i === 1 ? 'CEO — أرامكو السعودية' : 'إشارة ذكية',
      description: body.text ? `نتائج عن "${body.text}"` : 'وصف النتيجة',
      score: Math.max(0, 0.95 - i * 0.1),
      confidence: 0.9,
      highlights: [{ field: 'title', text: body.text ?? '', snippets: [body.text ?? ''] }],
      badges: [{ label: 'نشط', variant: 'success' }],
      actions: [{ id: 'view', label: 'عرض', handler: 'navigate' }],
      source: 'postgresql',
      updated_at: now,
    }))
    return HttpResponse.json({
      results, total: 42, page: 1, pageSize: 10,
      facets: [{ field: 'industry', label: 'القطاع', values: [{ value: 'energy', count: 15 }, { value: 'healthcare', count: 10 }] }],
      queryInterpretation: { original: body.text ?? '', interpreted: `نتائج عن "${body.text ?? ''}"`, entities: [], intent: 'search', confidence: 0.9 },
      timing: { total: 150, fullText: 50, semantic: 80, graph: 20, ai: 0, permissions: 0 },
    })
  }),

  http.post('/api/v1/search/suggest', async ({ request }) => {
    const body: any = await request.json()
    return HttpResponse.json({
      suggestions: [
        { text: `${body.prefix ?? ''} في قطاع الطاقة`, type: 'query', score: 0.95 },
        { text: `${body.prefix ?? ''} في الرياض`, type: 'query', score: 0.80 },
      ],
    })
  }),

  http.post('/api/v1/search/ai', async ({ request }) => {
    const body: any = await request.json()
    return HttpResponse.json({
      summary: `تحليل شامل للاستعلام: "${body.text ?? ''}"`,
      recommendations: ['مراجعة الفرص الحالية', 'التواصل مع صناع القرار'],
      risks: ['مخاطر السوق'],
      sources: [{ id: 'src1', title: 'تقرير ذكاء السوق', score: 0.92 }],
      confidence: 0.85,
      tokens: 450,
    })
  }),

  // ─── Companies ─────────────────────────────────────
  http.get('/api/v1/companies/:id', ({ params }) => {
    const company = companies.find((c) => c.id === params.id) ?? companies[0]
    return HttpResponse.json(company)
  }),
]

export default handlers
