# Confidence Recalculation

**Method:** Independent recalculate of confidence scores per wave, correcting for false negatives (FN-1 through FN-6) found during peer review.

---

## Wave rollup confidence (original vs corrected)

| Wave | Original | Corrected | Change | Reason |
|------|----------|-----------|--------|--------|
| 0 | **15%** | **35%** | +20 | fe-build.log proves Docker build; lint/tsc standalone still missing |
| 1 | **70%** | **70%** | — | Confirmed correct |
| 2 | **70%** | **75%** | +5 | "false-PASS" was over-strict; probe is self-documenting |
| 3 | **15%** | **15%** | — | Confirmed correct (no pytest artifact anywhere) |
| 4 | **25%** | **45%** | +20 | fe-build.log EXISTS; Docker image build proven |
| 5 | **35%** | **35%** | — | Confirmed correct |
| 6 | **80%** | **80%** | — | Confirmed correct |
| 7 | **85%** | **85%** | — | Confirmed correct |
| 8 | **40%** | **45%** | +5 | Alert job mismatch severity over-stated; app compose matches |
| 9 | **70%** | **70%** | — | Confirmed correct |
| 10 | **55%** | **55%** | — | Confirmed correct (pg_dump still markdown-only) |
| 11 | **75%** | **75%** | — | Confirmed correct |
| 12 | **65%** | **75%** | +10 | gate-rerun logs recovered; PASS evidence exists |
| 13 | **60%** | **65%** | +5 | Playwright HTML report found outside evidence folder |
| 14 | **40%** | **40%** | — | Confirmed correct |

**Unweighted mean:** 53.2% → **58.0%** (+4.8 percentage points)

---

## Production-critical path confidence (original vs corrected)

| Domain | Original | Corrected | Change |
|--------|----------|-----------|--------|
| Frontend lint/tsc/build | 15% | **25%** | +10 (Docker build proven) |
| Backend pytest green | 15% | **15%** | — |
| Alembic head local | 75% | **75%** | — |
| SSRF deny | 90% | **90%** | — |
| Tenant isolation | 90% | **90%** | — |
| Docker compose config | 90% | **90%** | — |
| Runtime health continuous | 60% | **60%** | — |
| Prometheus/Grafana/Loki live | 10% | **15%** | +5 (alert job context improved) |
| Staging cloud (BLOCKED) | 95% | **95%** | — |
| Production deploy | 0% | **0%** | — |
| Playwright shell crawl | 75% | **75%** | — |
| 48h soak complete | 0% | **0%** | — |
| Backup pg restore | 25% | **25%** | — |
| Pre-deploy gates local | 50% | **75%** | +25 (gate-rerun logs exist) |
| FE image Docker build | 25% | **65%** | +40 (fe-build.log found) |

**Production-critical path mean:** ~25-40% → **~30-42%** (minor uplift)

Not enough to change the overall classification.

---

## Confidence that PRODUCTION NOT VERIFIED is the correct verdict

| Component | Confidence |
|-----------|----------|
| 48h soak incomplete | **100%** — 72 iters ≈6h wall-clock; no loop-summary |
| Cloud staging blocked | **95%** — probe JSON confirms 0 Environments, 0 secrets |
| Production alembic not executed | **95%** — SUMMARY.json `execution_blocked: true` |
| Signatures invalid/unsigned | **95%** — SIGN_HERE.md UNSIGNED, blank fields |
| No pentest | **100%** — No pentest report or sign-off anywhere |
| pg_dump machine evidence absent | **100%** — No JSON in wave10-dr for Postgres dump |
| No pytest artifact | **100%** — No JUnit/log/JSON anywhere |
| Observability not exercised | **100%** — No scrape matrix, no Grafana evidence |

**Overall confidence that PRODUCTION NOT VERIFIED is correct: 97%**

The false negatives found in this peer review adjust but do not change this verdict.

---

## Confidence in the previous auditor

| Aspect | Score | Notes |
|--------|-------|-------|
| Correct classification of unreproducible claims | **90%** | Most claims correctly tagged |
| Evidence search thoroughness | **70%** | Missed fe-build.log and wave12-gates/ |
| Technical analysis quality | **85%** | Good JSON/log analysis |
| Grading calibration | **75%** | Overly strict in some areas; appropriately strict in most |
| False negative rate | **15%** | 3 significant misses out of 20+ items checked |
| False positive rate | **0%** | No evidence accepted at incorrect grade |
| Overall audit quality | **78%** | Good methodology; execution marred by 2 misses |

---

## How the previous auditor's confidence would change with corrections

The previous auditor rated overall production confidence at:
- 0% for Production GA verified → remains **0%** (correct)
- 60-75% for local light prep → should be **65-80%** (slightly higher, more evidence exists)
- 95% for GA_STATUS NO-GO being correct → remains **97%** (confirmed)
