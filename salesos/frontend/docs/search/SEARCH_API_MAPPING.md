# Universal Search Platform — API Mapping

## POST /api/v1/search

Primary search endpoint.

### Request
```json
{
  "text": "hospitals opening new branches",
  "types": ["company"],
  "filters": [{ "field": "industry", "operator": "eq", "value": "healthcare" }],
  "page": 1,
  "pageSize": 20,
  "sort": "relevance",
  "naturalLanguage": true
}
```

### Response
```json
{
  "results": [ /* SearchResult[] */ ],
  "total": 47,
  "page": 1,
  "pageSize": 20,
  "facets": [
    { "field": "industry", "label": "القطاع", "values": [ { "value": "healthcare", "count": 47 } ] }
  ],
  "queryInterpretation": {
    "original": "hospitals opening new branches",
    "interpreted": "شركات في قطاع الرعاية الصحية مع إشارات توسع حديثة",
    "intent": "search",
    "confidence": 0.85
  }
}
```

## POST /api/v1/search/suggest

### Request
```json
{ "prefix": "hos", "limit": 5 }
```

### Response
```json
{
  "suggestions": [
    { "text": "hospitals opening new branches", "type": "query", "score": 0.95 },
    { "text": "hospitals in Riyadh", "type": "query", "score": 0.80 }
  ]
}
```

## POST /api/v1/search/ai

### Request
```json
{ "text": "What are the risks with our top 5 suppliers?", "context": { "companyId": "comp_123" } }
```

### Response
```json
{
  "answer": {
    "summary": "تحليل المخاطر: …",
    "recommendations": ["مراجعة عقود الموردين", "…"],
    "risks": ["تركيز عالٍ على مورد واحد"],
    "sources": [ { "id": "comp_456", "title": "مورد الرياض", "score": 0.92 } ],
    "confidence": 0.78
  }
}
```

## Frontend Hook

```typescript
function useSearch(query: SearchQuery) {
  return useQuery({
    queryKey: searchKeys.results(query),
    queryFn: () => searchApi.search(query),
    enabled: query.text.length >= 2,
    staleTime: 30_000,
  })
}
```
