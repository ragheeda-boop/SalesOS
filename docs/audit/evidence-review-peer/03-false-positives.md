# False Positive Analysis

**Rule:** A false positive occurs when the previous auditor accepted evidence that should not count, or incorrectly graded evidence as higher quality than warranted.

---

## False positives found: 0 (zero)

After independent verification against the repository, **no false positives were found** in the previous audit. The auditor did not accept insufficient evidence as proof.

---

## Borderline cases reviewed

### BP-1: Wave 2 Load Probe confidence at 90%

**Auditor's classification:** Wave 2 SSRF deny → ✅ VERIFIED / confidence 90%

**Evidence:** `evidence/wave2-load/ssrf-denied-2026-07-22T125056Z.json` — JSON probe showing SSRF deny via `url_safety.py`

**Peer review:** The auditor's confidence of 90% is appropriate. The SSRF deny is backed by:
- Source code (`salesos/backend/app/services/url_safety.py`)
- Multiple probe JSON files (3 timestamps)
- The JSON contains actual HTTP response details

**Verdict:** NOT a false positive. Auditor correctly graded.

---

### BP-2: Neo4j dump/load confidence at 90%

**Auditor's classification:** Wave 10 Neo4j dump/load → ✅ VERIFIED / confidence 90%

**Evidence:** `neo4j-admin-dump-2026-07-22T102946Z.json`, `neo4j-admin-load-20260722T124100Z.json`

**Peer review:** The JSON files document:
- Dump: `dump_exit: 0`, `43 files, 257.9MiB processed in 31.957 seconds`
- Load: `node_count=0` (empty graph — fidelity limitation)
- Honest limitations documented

The load with `node_count=0` suggests the Neo4j load verification was mechanical (container starts, cypher runs) but doesn't prove data fidelity (empty graph). The auditor noted this limitation ("empty graph fidelity limit") while giving 90% for the mechanical exercise. This is reasonable since the audit was verifying the DR PROCEDURE works, not data fidelity.

**Verdict:** NOT a false positive. Auditor appropriately noted the limitation.

---

### BP-3: Wave 13 crawl report confidence at 75%

**Auditor's classification:** Wave 13 full UI crawl → 🟡 PARTIALLY VERIFIED / confidence 75%

**Evidence:** `full-ui-crawl-report.json` — 2767 lines with 49 pages, 136 clicks, all screenshots null

**Peer review:** 75% confidence is REASONABLE for a shell crawl. The report documents:
- 49/49 page shells loaded (HTTP 200)
- 14 pages with HTTP errors
- 34 pages with console errors
- 8 click failures
- All screenshots null
- `production_go: false`

The report is honest and machine-generated. 75% is appropriate for a shell-level crawl.

**Verdict:** NOT a false positive. Auditor appropriately downgraded for missing screenshots and API residuals.

---

### BP-4: Wave 11 4h soak confidence at 90-95%

**Auditor's classification:** Wave 11 4h loop 45 iters/16 FAIL/exit 1 → ✅ VERIFIED / confidence 95%

**Evidence:** `loop-summary-2026-07-22T142544Z.json` — 45 iterations, 16 failures, `soak_complete_claim: false`

**Peer review:** Confidence of 95% is appropriate. The JSON is machine-generated, honest about failures, and explicitly does NOT claim soak complete. The evidence quality is high.

**Verdict:** NOT a false positive.

---

### BP-5: Alembic migrations at 100% confidence

**Auditor's classification:** Wave 1 Alembic 0039/0040 files → ✅ VERIFIED / confidence 100%

**Evidence:** Source files in `salesos/backend/app/alembic/versions/0039_webhook_tables.py` and `0040_ensure_graph_tables.py`

**Peer review:** 100% confidence for file existence is appropriate. The files are in the repository and readable. SQL verify JSONs (wave11-soak/) confirm they were applied to local DB.

**Verdict:** NOT a false positive.

---

## Summary table: all false positive checks

| Auditor's claim | Grade given | Peer review | False positive? |
|----------------|-------------|-------------|-----------------|
| Wave 2 SSRF deny | ✅ VERIFIED / 90% | Correct | No |
| Wave 10 Neo4j dump/load | ✅ VERIFIED / 90% | Correct (limitation noted) | No |
| Wave 13 crawl | 🟡 PARTIALLY / 75% | Correct | No |
| Wave 11 4h soak | ✅ VERIFIED / 95% | Correct | No |
| Wave 1 Alembic files | ✅ VERIFIED / 100% | Correct | No |
| Wave 12 staging BLOCKED | ✅ VERIFIED / 95% | Correct | No |
| Wave 13 auth demo | 🟡 PARTIALLY / 75% | Correct | No |
| Wave 6 AI honesty source | ✅ VERIFIED / 100% | Correct | No |
| Wave 2 KG SQL fallback | ✅ VERIFIED / 90% | Correct | No |
| Wave 12 tabletop | 🟡 PARTIALLY / 75% | Correct | No |
| Wave 13 API residual probe | ✅ VERIFIED / 95% | Correct | No |

**Result: 0/11 items upgrade incorrectly → 0% false positive rate**

---

## What the auditor correctly DID NOT accept

The auditor correctly rejected or downgraded:

| Item | Auditor action | Correct? |
|------|---------------|----------|
| pg_dump SUCCESS from markdown | ❌ UNVERIFIED / 25% | Yes — no machine JSON |
| "1542 passed" without pytest log | ❌ UNVERIFIED / 25% | Yes — no JUnit/XML |
| "20 skipped" vs empty quarantine | 🚨 CONTRADICTED | Yes — factual contradiction |
| SIGN_HERE partial fill as GO | 🚨 CONTRADICTED | Yes — invalid signature |
| "build validated" without logs | 🚨 CONTRADICTED | Partially wrong — fe-build.log exists |
| Wave 7 DOCS "not executed" vs Wave 10 "executed" | 🚨 CONTRADICTED (stale) | Yes — documentation staleness |
| Security score "improved" | ❌ UNVERIFIED | Yes — no re-score artifact |
| Observability runtime | ❌ UNVERIFIED | Yes — not exercised |
| Production deploy | ❌ UNVERIFIED / 0% | Yes — not run |
| Cloud staging deploy | ✅ VERIFIED as BLOCKED | Yes — probe JSON proves blocked |

---

## Overall false positive rate

**0.0%** — No evidence was accepted at an unjustified confidence level. The auditor was appropriately skeptical.

Note: The flip side of this low false positive rate is the auditor's higher false negative rate (15%), suggesting the auditor was OVERLY STRICT at the cost of missing real evidence.
