# False Claims & Contradictions

**Audit date:** 2026-07-22  
**Rule:** PASS in markdown without matching artifacts, or PASS while sibling evidence shows failure, is a false positive.

---

## F1 — Wave 0 “build validated” without build evidence

| Item | Detail |
|------|--------|
| Claim | Lint/tsc/build exit 0; classification build validated |
| Evidence | NONE post-remediation; APPENDIX-A baseline **FAIL** |
| Classification | 🚨 CONTRADICTED as “build validated” |
| Correct label | **not validated** |

---

## F2 — Wave 2 load matrix overall PASS with HTTP 500s inside

| Item | Detail |
|------|--------|
| Claim | Probe matrix 26/26 PASS |
| Evidence | `probe-summary-2026-07-22T125056Z.json`: `"overall":"PASS"` while `competitors_network_http` shows competitors/network **500**; note says summary **reconstructed** after script `ArgumentException` |
| Classification | 🟡 false-PASS / PARTIALLY VERIFIED at best |
| Correct reading | SSRF/tenant checks strong; KG availability still failing at that timestamp |

---

## F3 — Wave 3 quarantine “20 skipped” vs empty QUARANTINE.txt

| Item | Detail |
|------|--------|
| Claim | Quarantine drives ~20 skips |
| Evidence | `salesos/backend/tests/unit/QUARANTINE.txt` is empty after “fix wave” |
| Classification | 🚨 CONTRADICTED (stale claim) |
| Correct reading | Skip count unknown without a current pytest log |

---

## F4 — Wave 4 FE rebuild Done vs INFRA Not run

| Item | Detail |
|------|--------|
| Claim A | `PROGRESS-WAVE4-FE-IMAGE.md` — rebuild Done |
| Claim B | `PROGRESS-WAVE4-8-9-INFRA.md` — FE rebuild Not run |
| Evidence | Cited `fe-build.log` **MISSING** |
| Classification | 🚨 CONTRADICTED between docs; rebuild **UNVERIFIED** |

---

## F5 — Wave 7 DOCS “Wave 10 not executed” vs Wave 10 “DRILL EXECUTED”

| Item | Detail |
|------|--------|
| Claim A | Wave 6–7 DOCS table: backup runbooks Executed? **No** |
| Claim B | Wave 10 backup progress / runbook: drill executed |
| Evidence for pg_dump | Still markdown-only (no JSON) |
| Classification | 🚨 CONTRADICTED (stale DOCS); pg_dump success still ❌ UNVERIFIED |

---

## F6 — Wave 8 alert job name vs root Prometheus scrape job

| Item | Detail |
|------|--------|
| Alerts | `up{job="salesos-backend"}` in `alerts.yml` / k8s rules |
| Root compose scrape | `prometheus.compose-root.yml` job_name **`salesos-api`** |
| salesos monitoring scrape | `prometheus.yml` job_name **`salesos-backend`** (matches alerts) |
| Classification | 🚨 CONTRADICTED for **root** compose path; split-brain risk |
| Impact | Root-stack alerts may never fire on intended target |

---

## F7 — Wave 10 headline pg_dump SUCCESS without machine evidence

| Item | Detail |
|------|--------|
| Claim | Local dump ~21.5 MiB, 431 TOC, restore row counts match |
| Evidence folder | `wave10-dr` has Neo4j/WAL JSON only — **no dump/restore JSON** |
| Classification | ❌ UNVERIFIED (markdown self-report) |
| Note | Treating markdown SUCCESS as PASS is a false positive |

---

## F8 — UI crawl “49/49 PASS” as product health

| Item | Detail |
|------|--------|
| Claim | Soft gate PASS; 49/49 page shells |
| Evidence | `full-ui-crawl-report.json`: `passCount:49`, but `pagesWithHttpErrors:14`, `pagesWithConsoleErrors:34`, `clicksFailed:8`, all `screenshot:null`, `afterLoginUrl` still `/login`, `production_go:false` |
| Classification | 🟡 PARTIALLY VERIFIED for shells; **false PASS** if narrated as full UI health |
| Correct label | light validated shell crawl with API residuals |

---

## F9 — SIGN_HERE partial GO fill while scoreboard NO-GO

| Item | Detail |
|------|--------|
| Header | **UNSIGNED**; agents must not forge |
| Body | CTO/TL blocks show `Status: SIGNED`, name filled, `Decision: [ ok] GO`, **Date blank**, **Signature blank**, evidence-reviewed unchecked |
| Classification | 🚨 CONTRADICTED as a valid Production GO signature |
| Correct reading | Invalid / incomplete form; **NO-GO** remains |

---

## F10 — 48h soak “started” narrated as progress toward GO without duration

| Item | Detail |
|------|--------|
| Honest docs | `soak_complete_claim: false`; NOT complete |
| Risk | Scoreboards listing “48h STARTED” can be misread as soak progress closing the blocker |
| Evidence | ~70 loop files ≈ ~6h wall-clock ≪ 48h; no summary |
| Classification | Docs mostly honest; **false positive if anyone claims 48h done** |

---

## F11 — Security score “improved” without re-score artifact

| Item | Detail |
|------|--------|
| Claim | Security improved from baseline 48 |
| Evidence | No scored re-audit JSON/report |
| Classification | ❌ UNVERIFIED (narrative) |

---

## F12 — Testing score “improved” via ~1542 without pytest artifact

| Item | Detail |
|------|--------|
| Claim | Unit ~1542; crawl 49/49 |
| Evidence | Crawl JSON exists; pytest count **no log** |
| Classification | Crawl partial; unit count ❌ UNVERIFIED |

---

## Summary table

| ID | Topic | Status |
|----|-------|--------|
| F1 | Build validated | 🚨 |
| F2 | Wave 2 26/26 PASS | 🟡 false-PASS |
| F3 | Quarantine 20 skips | 🚨 |
| F4 | FE rebuild Done/Not run | 🚨 |
| F5 | Wave 10 executed in DOCS | 🚨 stale |
| F6 | Prometheus alert job | 🚨 |
| F7 | pg_dump SUCCESS | ❌ |
| F8 | UI crawl product PASS | 🟡 false-PASS risk |
| F9 | SIGN_HERE GO | 🚨 |
| F10 | 48h complete | 🚨 if claimed |
| F11 | Security score delta | ❌ |
| F12 | 1542 tests | ❌ |

**None of the above authorize Production GO.**
