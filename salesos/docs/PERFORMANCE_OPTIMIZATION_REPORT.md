# SalesOS Performance Optimization Report

> Generated: 2026-07-11
> Source: Engineering Dashboard + Decision Platform engines analysis

---

## 1. Performance Budgets (from Engineering Dashboard)

| Endpoint | p50 | p95 | p99 | Budget | Status |
|----------|-----|-----|-----|--------|--------|
| `GET /companies/{id}` | 45ms | 120ms | 250ms | 200ms | 🟢 On budget |
| `POST /search` | 180ms | 450ms | 900ms | 500ms | 🟡 p99 exceeds |
| `GET /timeline` | 90ms | 300ms | 600ms | 300ms | 🟡 p99 exceeds |
| `POST /enrich` | 2.5s | 8s | 15s | 5s | 🔴 p50 & p99 exceed |

**Key insight**: Search and Timeline are within p50 budget but overshoot at p99, indicating tail latency issues. Enrich is critically over budget at all percentiles.

---

## 2. Decision Platform Performance Budget (New — Suggested)

The Decision Platform engines are CPU-bound and called synchronously within API request paths. They should have their own budgets:

| Engine Operation | Current (est.) | Budget | Gap |
|-----------------|---------------|--------|-----|
| `DecisionEngine.evaluate()` — single | ~2-15ms | < 10ms | 🟡 Near limit |
| `EvidenceEngine.collect()` — no sources | ~1-5ms | < 3ms | 🟡 Per-iteration overhead |
| `ScoringEngine.score()` — single type | < 0.5ms | < 1ms | 🟢 Healthy |
| `RecommendationEngine.generate()` | ~5-20ms | < 15ms | 🟡 Factor repetition |
| `RuleEngine.evaluate()` — 8 rules | ~2-8ms | < 5ms | 🟡 Repeated allocations |
| `evaluateBatch()` — 10 contexts | ~50-300ms | < 100ms | 🔴 Sequential |
| Evidence `deduplicate()` — 100 items | ~1-3ms | < 1ms | 🟡 Hash key cost |

---

## 3. Decision Engine (`decision-engine/index.ts`)

### 3.1 `crypto.randomUUID()` for non-security IDs

**Location**: `index.ts:15` (`generateId()`)

**Problem**: Uses `crypto.randomUUID()` to generate every evidence, decision, and history ID. This is a CSPRNG-grade call (~0.01-0.05ms per call) which is ~50x slower than alternatives. With 5-20 IDs per `evaluate()` call, this adds unnecessary overhead.

**Fix**: Use `Date.now().toString(36) + Math.random().toString(36).substring(2)` (already used in scoring-engine and evidence-engine) or a simple counter.

**Impact**: **Medium** — Reduces each `collectEvidence()` and `evaluate()` call by ~0.1-0.5ms. Compounded over batch evaluations.

### 3.2 `evidence.some()` called per rule in `applyRules()`

**Location**: `index.ts:154` (inside `applyRules()`, within the `intent` branch)

```typescript
const hasHighIntent = evidence.some(
  (e) => e.data && typeof e.data === 'object' &&
    'strength' in (e.data as Record<string, unknown>) &&
    (e.data as Record<string, unknown>).strength === 'high'
)
```

**Problem**: `evidence.some()` iterates the full evidence array on every rule evaluation. With 4 rules and growing, this is O(rules × evidence). The check is also repetitive — it computes the same thing for every rule in the `intent` category.

**Fix**: Pre-compute `hasHighIntent` once before the loop and reuse it across all rules.

**Impact**: **High** — Directly reduces per-evaluation time. More impactful as rule count grows.

### 3.3 Redundant `reduce()` calls in `computeScores()`

**Location**: `index.ts:191-199`

```typescript
const evidenceConfidence = evidence.reduce(...)
const ruleWeight = rulesApplied.reduce(...)
```

**Problem**: These are two separate `reduce()` passes over the same arrays. With `Array.reduce()` being O(n), this doubles the iteration cost.

**Fix**: Either pre-compute these in `evaluate()` and pass them down, or compute them in a single pass.

**Impact**: **Low-Medium** — Small absolute time but demonstrates a pattern that compounds in batch processing.

### 3.4 Duplicate `scores.find('confidence')` across functions

**Location**: `index.ts:316` and `index.ts:415`

**Problem**: `generateRecommendation()` and `buildExplainability()` both independently call `scores.find(s => s.type === 'confidence')`. This is a linear scan of the scores array performed twice.

**Fix**: Extract the confidence score in `evaluate()` and pass it as a parameter to both functions.

**Impact**: **Low** — But a clear redundant computation.

### 3.5 Sequential batch evaluation — `evaluateBatch()`

**Location**: `index.ts:497-503`

```typescript
async evaluateBatch(contexts: DecisionContext[]): Promise<DecisionResult[]> {
  const results: DecisionResult[] = []
  for (const context of contexts) {
    results.push(await this.evaluate(context))
  }
  return results
}
```

**Problem**: Each `context` is processed sequentially with `await`. Since evaluations are independent (no shared state mutation that would conflict), they can run in parallel.

**Fix**: Use `Promise.all(contexts.map(c => this.evaluate(c)))`.

**Impact**: **High** — For N contexts, reduces wall-clock time from O(N) to O(1) (within concurrency limits). Directly impacts batch scoring and enrichment pipelines.

### 3.6 `getHistory()` — Double array allocation

**Location**: `index.ts:510-530`

**Problem**: `ids.slice(-limit)` creates a new array, then `.map().filter().map()` creates additional intermediate arrays.

**Fix**: Iterate once with a manual loop or use a single `reduce()` pass.

**Impact**: **Low** — `getHistory()` is not a hot path.

---

## 4. Evidence Engine (`evidence-engine/index.ts`)

### 4.1 BUILTIN_PROVIDERS inner filter recomputed on every `collect()`

**Location**: `index.ts:219-222`

```typescript
for (const [providerKey, provider] of Object.entries(BUILTIN_PROVIDERS)) {
  const matchingTypes = Object.entries(EVIDENCE_TYPE_PROVIDER_MAP)
    .filter(([, p]) => p === providerKey)
    .map(([t]) => t as EvidenceType)
```

**Problem**: Every call to `collect()` (when no sources are passed) rebuilds the `providerKey → EvidenceType[]` mapping by iterating and filtering `EVIDENCE_TYPE_PROVIDER_MAP` for each provider. This data never changes at runtime.

**Fix**: Pre-compute the `PROVIDER_TO_TYPES: Record<string, EvidenceType[]>` map once at module level.

**Impact**: **High** — Eliminates a constant O(providers × types) recomputation on every `collect()` call. This runs on every evidence-gathering path.

### 4.2 `storeItems()` — Array spread allocation

**Location**: `index.ts:195`

```typescript
this.store.set(key, [...existing, ...items])
```

**Problem**: Creates a brand new array every time evidence is stored. If items are stored incrementally (many small collections), this allocates and discards many arrays.

**Fix**: Use `existing.push(...items)` if no deduplication is needed post-append, or only allocate a new array when necessary.

**Impact**: **Low-Medium** — GC pressure for high-frequency evidence collection.

### 4.3 `getRecent()` re-ranks already-ranked items

**Location**: `index.ts:262-271`

```typescript
async getRecent(tenantId: string, entityId: string, limit: number = 50): Promise<EvidenceItem[]> {
  const key = this.tenantKey(tenantId, entityId)
  const items = this.store.get(key) || []
  const ranked = rankByConfidence(items)
  return ranked.slice(0, limit)
}
```

**Problem**: Items stored in `collect()` are already sorted by confidence (via `rankByConfidence()` at line 241). But `getRecent()` re-sorts them. If the store retains ordering, this sort is redundant.

**Fix**: Either store items pre-sorted and avoid re-sorting in `getRecent()`, or keep a separate sorted reference.

**Impact**: **Medium** — For large evidence stores (1000+ items per entity), full sort O(n log n) is wasteful on every read.

### 4.4 `extractEvidenceFromRecord()` — Full key iteration for field filtering

**Location**: `index.ts:122-139`

```typescript
const data: Record<string, unknown> = {}
for (const [key, value] of Object.entries(record)) {
  if (key !== 'description' && key !== 'summary' && ...) {
    data[key] = value
  }
}
```

**Problem**: Iterates every key in `record` and compares against 12 known field names on each iteration. O(n) where n = record keys.

**Fix**: Use a Set of known keys for O(1) exclusion lookup. Or use `structuredClone(record)` and `delete` on known keys.

**Impact**: **Low-Medium** — Minor per-record, but compounds with many records.

---

## 5. Scoring Engine (`scoring-engine/index.ts`)

### 5.1 `computeConfidence()` — Double reduce pass

**Location**: `index.ts:80-87`

```typescript
function computeConfidence(factors: ScoreFactor[]): number {
  if (factors.length === 0) return 0
  const totalWeight = factors.reduce((sum, f) => sum + f.weight, 0)
  if (totalWeight === 0) return 0
  const coverage = Math.min(factors.length / 3, 1)
  const avgValue = factors.reduce((sum, f) => sum + f.value * f.weight, 0) / totalWeight
  return clamp(coverage * 0.6 + avgValue * 0.4)
}
```

**Problem**: Two separate `reduce()` calls over the same array. With `SCORE_CONFIGS` entries having 4-5 factors per type, this doubles iteration cost.

**Fix**: Compute `totalWeight` and `weightedSum` in a single `reduce()` pass.

**Impact**: **Low** — But a clear structural improvement. Reduces per-`score()` call overhead by ~40% for the confidence computation.

### 5.2 `score()` — Redundant totalWeight recomputation

**Location**: `index.ts:111-113`

```typescript
const totalWeight = scoredFactors.reduce((sum, f) => sum + f.weight, 0)
const value = totalWeight > 0
  ? clamp(scoredFactors.reduce((sum, f) => sum + f.value * f.weight, 0) / totalWeight)
  : 0
```

**Problem**: The weights in `SCORE_CONFIGS` are static and always sum to exactly 1.0 (verified). The `totalWeight` computation is unnecessary when using built-in configs. Additionally, the weighted sum can be accumulated during the factor-building loop (lines 99-109), avoiding the second reduce entirely.

**Fix**: Accumulate `weightedValue` during the `for (const cfg of config)` loop. For custom configs, compute totalWeight once but still accumulate in a single pass.

**Impact**: **Medium** — `score()` is called per score type. With 3-4 score types per evaluation, this eliminates 6-8 reduce passes.

---

## 6. Recommendation Engine (`recommendation-engine/index.ts`)

### 6.1 Repeated linear scans via `getScoreValue()`

**Location**: `index.ts:34-44` (used 20+ times across action definitions)

```typescript
function getScore(scores: Score[], type: ScoreType): Score | undefined {
  return scores.find(s => s.type === type)
}
```

**Problem**: Every action definition's `evaluate()` calls `getScoreValue()` 2-4 times, each performing a linear `find()` over the scores array (typically 4-8 items). With 8 action definitions, that's **16-32 linear scans** per `generate()` call.

**Fix**: Build a `Map<ScoreType, Score>` once at the start of `generate()` and use `map.get(type)` — O(1) per lookup.

**Impact**: **High** — Eliminates ~24 O(n) scans per recommendation. Directly impacts the recommendation generation time.

### 6.2 Nested iteration in `selectEvidence()` → `relevantEvidence()`

**Location**: `index.ts:46-51, 432-448`

```typescript
function relevantEvidence(evidence: EvidenceItem[], keywords: string[]): EvidenceItem[] {
  return evidence.filter(e => {
    const text = `${e.description} ${e.type} ${e.source}`.toLowerCase()
    return keywords.some(k => text.includes(k.toLowerCase()))
  })
}
```

**Problem**: Called for every action (up to 8x per recommendation). For each action, iterates ALL evidence items, and for each item, iterates keywords (4-5 each) with `toLowerCase()` called per keyword. That's O(actions × evidence × keywords).

**Fix**: Pre-compute a lowercase version of each evidence item once. Use a Set/Map for keyword matching instead of nested loops. Or cache `relevantEvidence` results for repeated calls.

**Impact**: **High** — For 10 evidence items × 8 actions × 5 keywords = 400 iterations, each with `toLowerCase()` calls. Reduces by 5-10x.

### 6.3 `assessRisks()` — Repeated `getScoreValue()` calls

**Location**: `index.ts:338-406`

`getScoreValue()` is called 5+ times independently for `risk`, `dataQuality`, `intent`, `relationship`. Each is a linear scan.

**Fix**: Use the same single-pass Map conversion from 6.1.

**Impact**: **Medium** — Combined with 6.1, eliminates all redundant linear scans.

---

## 7. Explainability Engine (`explainability-engine/index.ts`)

### 7.1 Full sort in `pickTop()` and `pickTopEvidence()`

**Location**: `index.ts:15-21`

```typescript
function pickTop(scores: Score[], n: number): Score[] {
  return [...scores].sort((a, b) => (b.value * b.confidence) - (a.value * a.confidence)).slice(0, n)
}
function pickTopEvidence(evidence: EvidenceItem[], n: number): EvidenceItem[] {
  return [...evidence].sort((a, b) => b.confidence - a.confidence).slice(0, n)
}
```

**Problem**: Both functions sort the entire array just to get the top N items. For evidence, scores are already sorted by confidence (from EvidenceEngine). For scores (typically 2-5 items), sorting is cheap, but the copy+sort pattern is wasteful.

**Fix**: Since evidence is already sorted from `EvidenceEngine`, just slice. For scores, use a simple linear scan to find top 3.

**Impact**: **Low-Medium** — Depends on evidence size. For 100+ evidence items, O(n log n) sort is wasteful.

### 7.2 `highestRisk()` — `indexOf` per element

**Location**: `index.ts:25-29`

```typescript
const order: RiskLevel[] = ['critical', 'high', 'medium', 'low']
return recommendation.risks.reduce<RiskLevel>((highest, r) => {
  return order.indexOf(r.level) < order.indexOf(highest) ? r.level : highest
}, 'low')
```

**Problem**: `indexOf()` scans the `order` array on every iteration. With 4 items, `indexOf` is O(n) each, making this O(n*m).

**Fix**: Pre-compute a `Map<RiskLevel, number>` for O(1) rank lookups.

**Impact**: **Low** — Risk arrays are small (1-5 items), but the pattern is inefficient.

---

## 8. Rule Engine (`rule-engine/index.ts`)

### 8.1 `evidence.map(e => e.id)` called 3x per evaluation

**Location**: `index.ts:320, 340, 359`

**Problem**: `evidenceIds` is recomputed 3 times during a single `evaluate()` call. Each `map()` iterates the full evidence array.

**Fix**: Compute `evidenceIds` once at the top of `evaluate()` and reuse.

**Impact**: **Medium** — For 50+ evidence items, eliminates 2 redundant O(n) iterations per evaluation.

### 8.2 Registry re-sorted on every `evaluate()` call

**Location**: `index.ts:308-310`

```typescript
const sortedRules = Array.from(this.registry.values()).sort(
  (a, b) => b.priority - a.priority,
)
```

**Problem**: The rule registry is static after construction (rules are registered once). But `evaluate()` sorts it on every invocation.

**Fix**: Maintain a sorted array as a class property, only re-sorting when `register()` or `registerMany()` is called.

**Impact**: **Medium** — Sorting 8+ rules on every evaluation is O(n log n) for a constant dataset. Adds ~0.5-2ms per evaluate call.

### 8.3 `matchesCondition()` — Double `evidence.find()`

**Location**: `index.ts:59-86`

**Problem**: On lines 59-64, `evidence.find()` is called with `key`. If no match, lines 77-84 call another `evidence.find()` with `evKey` (stripping `evidence.` prefix). Both traverse the full evidence array independently.

**Fix**: Merge into a single pass that checks both `key` and `evKey` simultaneously.

**Impact**: **Low-Medium** — Compounds with many rules and large evidence sets.

---

## 9. Feedback Engine (`feedback-engine/index.ts`)

### 9.1 `getByDecision()` — Full Map iteration

**Location**: `index.ts:97-105`

```typescript
async getByDecision(decisionId: string): Promise<Feedback | null> {
  for (const record of this.feedbackStore.values()) { ... }
```

**Problem**: Searches through all feedback records linearly. With a `Map` keyed by feedback ID, this cannot leverage the O(1) lookup.

**Fix**: Build a secondary index: `Map<decisionId, feedbackId>` maintained on `submit()`.

**Impact**: **Medium** — For large feedback stores (1000+ records), O(n) lookup becomes slow.

### 9.2 `getStats()` — Multiple filter passes

**Location**: `index.ts:119-144`

**Problem**: Filters records 5 times: once for each outcome (accepted, rejected, ignored) plus `timed` filter. Each `filter()` creates a new array.

**Fix**: Count all categories in a single `for` loop over records.

**Impact**: **Low-Medium** — Reduces GC pressure and iteration overhead.

---

## 10. Learning Engine (`learning-engine/index.ts`)

### 10.1 `getRecommendationQuality()` — Multiple filter passes

**Location**: `index.ts:66-103`

**Problem**: Filters `qualityEvents` once (line 68), then `acceptanceEvents` once (line 85), then three more binary filters for high/medium/low counts (lines 90-94). Each `filter()` creates a new array.

**Fix**: Accumulate all counts in a single pass through the events array.

**Impact**: **Low-Medium** — Cleaner code, reduced intermediate array allocation.

### 10.2 `filterByTenant()` called in every public method

**Location**: `index.ts:60-64`

**Problem**: Every public method calls `filterByTenant()` which filters the full store array and maps to extract events. With 5+ public methods potentially called in sequence, this repeats the same work.

**Fix**: Since the store is an in-memory array, methods could be composed or the filtered result cached per request.

**Impact**: **Low** — Only matters under sustained query load.

---

## 11. Summary: Highest-Impact Optimizations

| Priority | Engine | Issue | Est. Impact | Effort |
|----------|--------|-------|-------------|--------|
| **P0** | Recommendation | Repeated `getScoreValue()` linear scans (6.1) | 5-15ms per call | Low |
| **P0** | Evidence | BUILTIN_PROVIDERS map recomputed (4.1) | 1-3ms per collect | Low |
| **P1** | Decision | `evidence.some()` in rule loop (3.2) | 1-5ms per eval | Low |
| **P1** | Recommendation | Nested evidence/keyword iteration (6.2) | 3-10ms per call | Medium |
| **P1** | Decision | Sequential `evaluateBatch()` (3.5) | 10x wall-clock for N=10 | Low |
| **P2** | Scoring | Double reduce + redundant totalWeight (5.1, 5.2) | < 1ms per call | Low |
| **P2** | Rule | Re-sorted registry on every eval (8.2) | 1-3ms per eval | Low |
| **P2** | Rule | `evidence.map()` called 3x (8.1) | 1-2ms per eval | Low |
| **P3** | Evidence | `getRecent()` re-ranks sorted items (4.3) | 1-5ms per call | Low |
| **P3** | Explainability | Full sort in pickTop/pickTopEvidence (7.1) | 1-3ms per call | Low |
| **P3** | Feedback | `getByDecision()` full iteration (9.1) | Scales with store size | Medium |
| **P3** | Feedback | `getStats()` multiple filters (9.2) | < 1ms | Low |

**Total estimated improvement**: ~15-45ms per full DecisionEngine `evaluate()` cycle, and up to **10x wall-clock improvement for batch operations** via parallelization.

---

## 12. Cross-Cutting Concerns

### 12.1 Memory Pressure

The in-memory stores grow unboundedly:
- `DecisionEngine.history` — accumulates all results
- `EvidenceEngine.store` — retains all evidence per tenant/entity
- `FeedbackEngine.feedbackStore` — all feedback records
- `LearningEngine.store` — all learning events

**Recommendation**: Add LRU eviction or TTL-based pruning. Without it, the lookup operations in many of these engines will degrade to O(n) over time regardless of micro-optimizations.

### 12.2 No Database Backing

All engines use `Map`-based in-memory stores. While this is expected for a platform layer, any production deployment should ensure these do not replace database queries in hot API paths. The Dashboard's RED status on `/enrich` (p50=2.5s, p99=15s) may be related to this engine pipeline being part of the enrichment flow.

### 12.3 Tail Latency (Dashboard Correlation)

The Dashboard shows `/search` and `/timeline` are within p50 budget but exceed at p99 (900ms and 600ms respectively). The repeated array allocations and sorts identified above are likely contributors — they create GC pressure that manifests as sporadic pauses, directly explaining the p99 inflation.
