# Architectural Drift — EAB-2026-08-06-001 (Axis 41)

**Validation:** light validated (manual counts from Grep/Read)  
**First pack baseline** — rate/month (G-03) not computable until next run

---

## DM metrics

| Metric | Value | Notes / evidence |
|--------|------:|------------------|
| DM-01 ADR–impl mismatch | **4** | ADR-101 missing; ADR-102 Kafka claim vs compose; ADR-033 STUB; ADR-028 completeness open |
| DM-02 Orphan ADRs | **3** | engineering-os ADRs cited in index, tree empty/absent |
| DM-03 Orphan capabilities | **2** | marketplace tip stubs; FE decision twin orphaned from FE resolve |
| DM-04 Dual-engine clusters | **4** | decision (≥3 BE), search (2), webhooks (≥3), prompt registries (≥3) |
| DM-05 Dual compose | **1** | root `docker-compose.yml` vs `salesos/docker-compose.yml` (+≥7 compose files total) |
| DM-06 Orphan MetaData | **≥18** | `MetaData(` count across backend files |
| DM-07 Bible–audit delta | **2** | dual bibles; AI-native language vs AI_HONESTY / NO-GO |
| DM-08 DTM breaks | **8** | sample rows with ≥1 break (see DECISION-TRACEABILITY.md) |
| DM-09 Superseded citations | **3** | GO_NO_GO_DECISION, GA_CHECKLIST, G04_AI_VALIDATION still on disk |
| DM-10 AI honesty breaches | **0** hard | Flags/STUB labeled; dual package name = **proxy risk** not counted as breach |

### Formula (default weights from 07-SCORING-MODEL)

```text
w = (3,2,2,4,3,3,2,3,2,5)
raw = 3*4 + 2*3 + 2*2 + 4*4 + 3*1 + 3*18 + 2*2 + 3*8 + 2*3 + 5*0
    = 12 + 6 + 4 + 16 + 3 + 54 + 4 + 24 + 6 + 0
    = 129
drift_score = max(0, 100 - min(100, 129)) = 0
```

| Field | Value |
|-------|------:|
| raw | **129** |
| drift_score | **0** |
| Dominant term | DM-06 MetaData (54) + dual engines (16) + DTM breaks (24) |

**Reading:** Severe measured drift on first baseline. Improving MetaData and collapsing dual engines will move score most.

---

## Fitness catalog pass/fail/unknown

| ID | Result | Notes |
|----|--------|-------|
| FF-01 | unknown | No import-linter run |
| FF-02 | unknown | No cycle detect run |
| FF-03 | fail | Many caps without ADR; DECs compensate partially |
| FF-04 | unknown | OpenAPI coverage not exhaustively checked |
| FF-05 | unknown | Event catalog incomplete this run |
| FF-06 | unknown | CODEOWNERS not fully verified |
| FF-07 | **pass** | `feature_ai_copilot=False`; FE decision STUB labeled |
| FF-08 | **fail** | Lifetime sessions + BYPASSRLS fallback |
| FF-09 | **fail** | Dual compose + ≥18 MetaData flagged |
| FF-10 | **fail** | Middleware fail-open if factory unset |
| FF-11 | unknown | FE build verify not executed (low-load) |
| FF-12 | fail | Superseded GO docs still present/citeable |
| FF-13 | fail | DTM sample incomplete |
| FF-14 | **pass** (partial) | DecisionProvider prefers HTTP; do not use STUB evaluate |

**Activated in CI:** 0% (EAB-001-P2-FIT-01)

---

*Drift — EAB-2026-08-06-001*
