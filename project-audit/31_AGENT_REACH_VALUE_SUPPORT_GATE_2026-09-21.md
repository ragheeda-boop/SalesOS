# 31 — Agent Reach proposed-value support gate — 2026-09-21

## Finding

The proposal bridge already checked tenant, expiry, source URL, and exact company-name linkage, but it did not check that the proposed fact appeared anywhere in the persisted evidence. As a result, a caller could attach valid evidence about a company while proposing an unrelated value.

## Change

- Added a bounded lexical check requiring a proposed scalar string to appear as a whole phrase in the stored evidence title or summary. Comparison uses Unicode NFKC normalization and case folding; substring-only matches such as `Riya` inside `Riyadh` are rejected.
- Unsupported types, empty text, values above 512 characters, and values absent from captured title/summary fail closed before a Fact Review proposal is written.
- This is a relevance screen, not semantic truth verification. A phrase in an Agent Reach summary can still be inaccurate. Evidence remains `CITED_CLAIM` / `UNKNOWN` at 0.40, human review remains mandatory, and CRM remains unchanged.
- The check consumes only already-persisted evidence and does not call a provider or copy `raw_data`.

## Verification

- Combined focused unit/security and PostgreSQL regression: **83/83 PASS**. Breakdown: **80 unit/security** and **3 PostgreSQL integration** tests, including a persisted-evidence negative case for an unrelated proposed city.
- Ruff E4/E7/E9/F/I and `compileall`: **PASS**.
- PostgreSQL tests ran only against `salesos_test` with `salesos_app` (non-superuser, non-BYPASSRLS); integration fixtures rolled back. Existing spend tests also prove every spend table remains empty after cleanup.
- No browser, production database, provider, staging, deployment, CRM auto-apply, or commit was used.

## Remaining work

1. Add provider-specific validators for types and claims that need normalization (for example, phone, email, dates, and numeric counts) before any provider adapter is enabled.
2. Add an independent semantic/source authenticity check where provider contracts and source payloads permit it. Lexical occurrence alone is insufficient proof.
3. Preserve human Fact Review and keep approved-fact CRM apply separate and atomic.

Roadmap remains **46%** (52/113 at last full census; no recensus); Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.
