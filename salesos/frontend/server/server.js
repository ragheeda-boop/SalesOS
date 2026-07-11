const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
app.use(express.json());

const now = new Date().toISOString();

// Dashboard
app.get('/api/v1/dashboard', (req, res) => {
  res.json({
    generatedAt: now, period: 'today', totalTracked: 127,
    missionCenter: { data: { mission: 'زيادة الإيرادات بنسبة 15% هذا الربع', progress: 62, keyResults: [{ label: 'الصفقات المغلقة', current: 18, target: 25 }, { label: 'الاجتماعات', current: 42, target: 60 }], updatedAt: now }, status: 'ready' },
    decisionQueue: { data: { decisions: [{ id: 'd1', title: 'متابعة شركة الطاقة', priority: 'high', impact: '500K', due: now, status: 'pending' }] }, status: 'ready' },
    intelligenceFeed: { data: { items: [{ id: 'i1', type: 'signal', title: 'إشارة توسع', severity: 'high', timestamp: now }] }, status: 'ready' },
    aiBrief: { data: { summary: '3 فرص استراتيجية جديدة', highlights: ['شراكة محتملة'], generatedAt: now }, status: 'ready' },
    marketPulse: { data: { topMovers: [{ name: 'قطاع الطاقة', change: 2.5 }], trends: ['ارتفاع الطلب'] }, status: 'ready' },
    recentActivity: { data: { items: [{ id: 'a1', type: 'meeting', title: 'اجتماع', companyName: 'أرامكو', timestamp: now }], total: 1 }, status: 'ready' },
  });
});

// Company Intelligence
app.get('/api/v1/companies/:id/intelligence', (req, res) => {
  res.json({
    companyId: req.params.id, generatedAt: now,
    dna: { industry: 'energy', businessModel: 'b2b', size: { employees: 15000, revenue: '1.2B', label: 'enterprise' }, growthPattern: 'accelerating', buyingBehaviour: { score: 78, intent: 'high' }, technologyProfile: { erp: 'sap' }, financialHealth: { score: 82, revenue: 1200000000, growth: 12.5, trend: 'up' }, governmentExposure: { level: 'high', contracts: 45 }, expansionPotential: { score: 72, markets: ['UAE'] }, digitalPresence: { score: 68, website: 'active', social: 'active' }, hiringTrend: { trend: 'growing', openings: 120 }, procurementMaturity: { score: 65, level: 'managed' }, relationshipStrength: { score: 70, connections: 15 }, buyingIntent: { score: 82, confidence: 0.88 }, riskLevel: { score: 25, level: 'low' }, confidenceScore: 0.92, dataFreshness: { score: 90, updatedAt: now }, goldenRecordStatus: { status: 'clean', sources: 5 } },
    aiRecommendation: { action: 'meeting', actionLabel: 'ترتيب اجتماع', reasoning: 'ارتفاع نية الشراء', confidence: 0.85, expectedRevenue: 500000, expectedImpact: 'high', estimatedTime: 'أسبوعين', alternatives: [], risks: ['مورد بديل'] },
    decisionMakers: [{ id: 'dm1', name: 'د. أحمد', role: 'CEO', department: 'الإدارة', influence: 'high', connected: true }],
    relationships: { nodes: [{ id: 'n1', type: 'person', label: 'د. أحمد', strength: 0.9 }], edges: [] },
    timeline: [{ id: 't1', type: 'signal', summary: 'إعلان توسع', date: now, source: 'News', aiHighlighted: true }],
    signals: [{ id: 's1', type: 'hiring', title: 'توظيف كبير', description: '', source: 'LinkedIn', severity: 'high', timestamp: now, aiConfidence: 0.92 }],
    government: [{ id: 'g1', type: 'cr', title: 'السجل التجاري', status: 'active', source: 'وزارة التجارة', confidence: 0.95, freshness: now }],
    documents: [{ id: 'd1', title: 'عقد توريد', type: 'contract', date: now, aiSummary: 'ملخص العقد', confidence: 0.92 }],
    buyingJourney: { currentStage: 'evaluation', progress: 45, timeInStage: '14 يوم', recommendedAction: 'تقديم عرض', stageDescription: 'تقييم الموردين' },
    goldenRecord: [{ id: 'gr1', entityName: 'شركة', source: 'CRM', confidence: 0.98, conflicts: [], freshness: now, status: 'matched' }],
  });
});

// Search
app.post('/api/v1/search', (req, res) => {
  const results = Array.from({ length: 5 }, (_, i) => ({
    id: `r_${i}`, entity_type: i === 0 ? 'company' : 'signal',
    title: i === 0 ? 'شركة أرامكو' : `إشارة ${i}`,
    subtitle: 'وصف', score: Math.max(0, 0.95 - i * 0.1), confidence: 0.9,
    highlights: [], badges: [{ label: 'نشط', variant: 'success' }],
    actions: [{ id: 'view', label: 'عرض', handler: 'navigate' }],
    source: 'postgresql', updated_at: now,
  }));
  res.json({ results, total: 42, page: 1, pageSize: 10, facets: [], timing: { total: 150, fullText: 50, semantic: 80, graph: 20, ai: 0, permissions: 0 } });
});

app.post('/api/v1/search/suggest', (req, res) => {
  res.json({ suggestions: [{ text: `${req.body.prefix} في الطاقة`, type: 'query', score: 0.95 }] });
});

app.post('/api/v1/search/ai', (req, res) => {
  res.json({ summary: `تحليل: ${req.body.text}`, recommendations: ['التواصل'], risks: [], sources: [], confidence: 0.85, tokens: 450 });
});

const PORT = 3001;
app.listen(PORT, () => console.log(`SalesOS API running on port ${PORT}`));
