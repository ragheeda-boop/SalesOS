# Company Intelligence Command Center — API Mapping

## GET /api/v1/companies/{id}/intelligence

Full intelligence payload for the command center.

### Response
```json
{
  "companyId": "comp_123",
  "generatedAt": "2026-07-10T12:00:00Z",
  "dna": {
    "industry": "energy",
    "businessModel": "b2b",
    "size": { "employees": 15000, "revenue": "1.2B" },
    "growthPattern": "accelerating",
    "buyingBehaviour": { "score": 78, "intent": "high" },
    "technologyProfile": { "erp": "sap", "crm": "salesforce", "cloud": "azure" },
    "financialHealth": { "score": 82, "revenue": "1.2B", "growth": 12.5 },
    "governmentExposure": { "level": "high", "contracts": 45 },
    "expansionPotential": { "score": 72, "markets": ["UAE", "Egypt"] },
    "digitalPresence": { "score": 68, "website": "active", "social": "active" },
    "hiringTrend": { "trend": "growing", "openings": 120 },
    "procurementMaturity": { "score": 65, "level": "managed" },
    "relationshipStrength": { "score": 70, "connections": 15 },
    "buyingIntent": { "score": 82, "confidence": 0.88 },
    "riskLevel": { "score": 25, "level": "low" },
    "confidenceScore": 0.92,
    "dataFreshness": { "score": 90, "updatedAt": "2026-07-10T11:00:00Z" },
    "goldenRecordStatus": { "status": "clean", "sources": 5 }
  },
  "aiRecommendation": {
    "action": "schedule_demo",
    "reasoning": "ارتفاع نية الشراء مع توفر جهات اتخاذ القرار",
    "confidence": 0.85,
    "expectedRevenue": 500000,
    "expectedImpact": "high",
    "estimatedTime": "2 weeks",
    "alternatives": [ { "action": "send_proposal", "confidence": 0.7 } ],
    "risks": [ "مورد بديل قيد التقييم" ]
  },
  "decisionMakers": [
    { "id": "dm_1", "name": "د. أحمد السلمي", "role": "CEO", "influence": "high", "connected": true }
  ],
  "timeline": [
    { "id": "evt_1", "type": "signal", "summary": "إعلان توسع", "date": "2026-07-10", "source": "news" }
  ],
  "signals": [],
  "government": [],
  "documents": [],
  "buyingJourney": {
    "currentStage": "evaluation",
    "progress": 45,
    "timeInStage": "14 days",
    "recommendedAction": "تقديم عرض توضيحي"
  },
  "goldenRecord": {
    "status": "clean",
    "sources": 5,
    "confidence": 0.95,
    "lastMerged": "2026-07-09"
  }
}
```

## Frontend Hook

```typescript
function useCompanyIntelligence(companyId: string) {
  return useQuery({
    queryKey: ['company-intelligence', companyId],
    queryFn: () => fetchCompanyIntelligence(companyId),
    enabled: !!companyId,
    staleTime: 30_000,
  })
}
```
