# Corrected Wave Status

**Peer review corrections to the previous auditor's wave verification matrix.**

**Legend:**  
✅ VERIFIED | 🟡 PARTIALLY VERIFIED | ❌ UNVERIFIED | 🚨 CONTRADICTED  
**Bold** = peer-corrected from original

---

## Wave 0 — Frontend unblockers

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| `npm run lint` exit 0 | ❌ UNVERIFIED | ❌ UNVERIFIED | No standalone lint log; only Docker build exists |
| `npx tsc --noEmit` exit 0 | ❌ UNVERIFIED | ❌ UNVERIFIED | No standalone tsc log |
| `npm run build` exit 0 (51 pages) | ❌ UNVERIFIED | 🟡 **PARTIALLY VERIFIED** | `fe-build.log` shows Docker `next build` succeeded |
| Classification "build validated" | 🚨 CONTRADICTED | 🟡 **PARTIALLY VERIFIED** | `fe-build.log` exists; Docker build evidence was missed |
| Hooks/lint source fixes present | 🟡 PARTIALLY VERIFIED | 🟡 PARTIALLY VERIFIED | Unchanged |
| Dashboard routes exist | ✅ VERIFIED | ✅ VERIFIED | Unchanged |

**Confidence adjustment:** Wave 0 rollup: 15% → **35%** (Docker build evidence recovered)

---

## Wave 4 — FE image + infra

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| `docker compose build frontend` exit 0 | ❌ UNVERIFIED | 🟡 **PARTIALLY VERIFIED** | `fe-build.log` EXISTS at cited path; image built successfully |
| FE routes /, /copilot, /analytics → 200 | 🟡 PARTIALLY VERIFIED | 🟡 PARTIALLY VERIFIED | Unchanged |
| Compose healthchecks / Neo4j HTTP probe | 🟡 PARTIALLY VERIFIED | 🟡 PARTIALLY VERIFIED | Unchanged |
| Stack `up` + `/health/detailed` | ❌ UNVERIFIED | ❌ UNVERIFIED | Unchanged |
| INFRA: FE rebuild Not run vs FE-IMAGE: Done | 🚨 CONTRADICTED | 🟡 **PARTIALLY VERIFIED** | Build log reconciles: rebuild was Done (Docker) |
| Hardcoded prometheus JWT removed | ✅ VERIFIED | ✅ VERIFIED | Unchanged |

**Confidence adjustment:** Wave 4 rollup: 25% → **45%** (build log recovered)

---

## Wave 12 — Gates / staging / migrate

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| `pre-deploy-gates.ps1` exists | ✅ VERIFIED | ✅ VERIFIED | Unchanged |
| Gates runtime PASS | 🟡 PARTIALLY VERIFIED | ✅ **VERIFIED** | `evidence/wave12-gates/` EXISTS with 4 PASS logs |
| Local deploy/rollback tabletop | 🟡 PARTIALLY VERIFIED | 🟡 PARTIALLY VERIFIED | Unchanged |
| Staging cloud BLOCKED | ✅ VERIFIED | ✅ VERIFIED | Unchanged |
| Virtual staging :8001/:3002 | ✅ VERIFIED | ✅ VERIFIED | Unchanged |
| Prod migrate executed: false | ✅ VERIFIED | ✅ VERIFIED | Unchanged |
| Backend image bake digests | ❌ UNVERIFIED | ❌ UNVERIFIED | Unchanged |

**Confidence adjustment:** Wave 12 rollup: 65% → **75%** (gate-rerun logs recovered)

---

## Wave 13 — Auth / UI / crawl

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| Playwright UI smoke PASS | ❌ UNVERIFIED | 🟡 **PARTIALLY VERIFIED** | `playwright-report/index.html` exists, not in evidence folder |
| Crawl screenshots | 🚨 CONTRADICTED | 🚨 CONTRADICTED | All screenshots null; 0 PNGs. Unchanged. |

**Confidence adjustment:** Wave 13 rollup: 60% → **65%** (Playwright report found outside evidence)

---

## Wave 2 — Load probes

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| Probe matrix 26/26 PASS (T125056Z) | 🟡 false-PASS / 50% confidence | 🟡 **PARTIALLY VERIFIED / 70% confidence** | Probe documents residuals transparently; PASS reflects probe checks, not system health |

---

## Wave 8 — Observability

| Claim | Original status | **Corrected status** | Reason |
|-------|----------------|---------------------|--------|
| Alerts match root scrape job | 🚨 CONTRADICTED | 🟡 **PARTIALLY VERIFIED** | SalesOS compose matches alerts perfectly; root compose is dev-only. Contradiction real for root compose but low severity. |

---

## Corrected verification summary

| Wave | Original | Corrected | Change |
|------|----------|-----------|--------|
| 0 | 🚨/❌ | 🟡/❌ mixed | Confidence 15% → 35% |
| 4 | 🚨/❌ | 🟡/🟡 mixed | Confidence 25% → 45% |
| 12 | 🟡 | ✅ gates; 🟡 rest | Confidence 65% → 75% |
| 13 | ❌/🚨 | 🟡/🚨 | Confidence 60% → 65% |
| 2 | 🟡 (50%) | 🟡 (70%) | False-PASS over-strict |
| 8 | 🚨 | 🟡 | Severity over-stated |

**Overall adjusted unweighted mean:** ~53% → **~58%** (minor uplift from corrected false negatives)

**Production-critical path:** remains ≈25-40% (no change — blockers still stand)

---

## Waves with NO correction needed

Waves 1, 3, 5, 6, 7, 9, 10, 11, 14 — the previous auditor's classifications are **confirmed correct**. No evidence was missed in these waves.
