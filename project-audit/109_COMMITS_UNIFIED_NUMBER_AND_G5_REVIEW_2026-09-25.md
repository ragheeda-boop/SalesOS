# 109 — Protective commits, unified-number label, and the G5 real-world review (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026: "يلا , وانت فريقي الي حيقوم بالفحص كذالك". This approves the commit batches and the unified-number fix, and **delegates the G5 review to the agent**.
**Scope:** local git commits (no push), code, and web checks of public company sites. No production writes, no Google Maps (banned, report 29), no Apollo or enrichment providers, no government registry APIs.

## 1. Commits (report 100 plan)

| # | Commit | Content |
|---|---|---|
| 1 | `0367e39d` | `.gitignore`: also newly ignores `salesos/backend/app/modules/identity/_keys/` (a **private RSA signing key** that was untracked and exposed to any broad `git add`) |
| 2 | `4adee846` | The 30 missing migrations (chain verified: 129 files, single head `f2e3d4c5b6a7`, no missing parents) plus `app/modules/facts/{__init__,models}.py`, which `env.py` imports |
| 3 | `be960736` | Master Data platform: `master_data/**`, `entity_resolution/**`, `facts/**`, and the Phase 6/7 and MUHIDE scripts (67 files) |

- **Identity:** git had no user configured. Commits use the repository's existing author `ragheed-AQLIYA <ragheed@aqliya.com>` via per-command environment variables. Git config was not modified.
- **Checks:** secret-pattern scan and a large-file scan per batch. The only credential found is `salesos_dev_password`, the local dev default already tracked in `.env.example` / `docker-compose.yml`.
- **Batches 4–7 blocked:** the remaining backend code, tests, frontend and docs were **blocked by the permission classifier**, because they are a bulk commit of mixed parallel-session work without hunk review. Not retried or worked around. They need the owner's direct approval or a per-hunk review.
- A stale `.git/index.lock` (0 bytes, from 00:43, no git process) was removed.
- Nothing was pushed.

## 2. Unified national number (third systematic finding)

Among 10-digit registry numbers from non-NCNP sources, **19,322 of 20,014 (96.5%) start with 7**, the unified national number (700) series. They come from SFDA (18,930) and SOCPA (362). Real CRs (1010…, 4030…, etc.) number about 692, mostly from Engineering Offices.

- **Fix (display only):** `GlobalCompanyResponse.cr_number_kind` returns `UNIFIED_NATIONAL_NUMBER` / `COMMERCIAL_REGISTRATION` / `UNKNOWN`. The V3 companies table shows it under the header "Registry number".
- **Classification is unchanged:** treating 7-series numbers as non-CR would remove identity from about 11k accounts, because `unified_national_number` is not an identity signal in OPTION C. That would be a separate PO decision.
- **Tests:** unit 3/3; frontend typecheck + ESLint pass.

## 3. G5 real-world spot check (SRWR, 51 accounts)

**Method:**
- Each account's identity basis (entity domain vs registry number) was derived first.
- Domain accounts: the company website was fetched and compared with name, activity and city.
- Registry-number accounts and dead domains: public web search.

**Decisions** are in `G5_SRWR_REAL_WORLD_SPOT_CHECK.csv`, each with evidence URL and note. Reviewer is marked `Claude (agent) - delegated reviewer for Ragheed Almadani (PO); AGENT-EXECUTED`.

| Result | Count |
|---|---:|
| CORRECT | 23 (of which **8 are foreign companies**, OUT_OF_MARKET: Iraq, India, UK×2, Italy, Germany, USA, Sweden) |
| MATERIAL_ERROR | **6** (all WRONG_DOMAIN: law firm, site builder, unrelated site, disposable-mail-style domain, UK recruiter, different restaurant company) |
| CANNOT_VERIFY | 22 (dead/parked/under-construction domains; registry-number accounts not found by web search) |

**Material error rate: 6/51 = 11.8%** (6/29 = 20.7% of the verifiable accounts). This is far above the 2% threshold. **Recommendation: do NOT accept the SALES_READY_WITH_REVIEW stratum.**

Only 15/51 (29%) are both verified and in-market Saudi companies.

### Why it fails (patterns, not one-offs)

1. **Single-source domains taken from a contact email.** Five of the six errors are a third party's domain: a lawyer, a website builder, another company. A domain from one source, never corroborated, is weak identity.
2. **Foreign Apollo accounts.** 8 of 16 Apollo-only accounts are non-Saudi companies. The 16% share is identity-correct but commercially irrelevant.
3. **Dead domains.** Many domains no longer resolve, or are parked or under construction.
4. **Registry-number-only accounts** cannot be verified without a registry. Web presence of small Saudi establishments is thin.

### Proposed next steps (need a PO decision)

- **A.** An OPTION C amendment: a single-source domain is not enough for SALES_READY_WITH_REVIEW. It needs corroboration (Apollo, a second source, or a matching registry number); otherwise ENRICHMENT_REQUIRED.
- **B.** A market filter: Apollo accounts whose HQ country is not Saudi Arabia (and no Saudi source) → `OUT_OF_MARKET` blocker.
- **C.** A domain liveness check (DNS resolution) as a derived signal. Dead domain → not an identity signal.
- **D.** Re-draw and repeat the G5 spot check after A–C. The expected error rate after these fixes needs measuring, not assuming.

G4 review is **not started**, pending this decision, because A and C also change the P1 populations.

## 4. Verification

- Unit tests: 3/3 schema.
- Capture tool dry run: G5 reviewed 51, material errors 6, 11.76%, `within_2pct_threshold: false`.
- No database writes in this report's work (G5 has no per-row queue).

Gates G3/G4/G5 remain **OPEN**; G5 SRWR **recommended REJECT**. Production is **NOT APPROVED**.
