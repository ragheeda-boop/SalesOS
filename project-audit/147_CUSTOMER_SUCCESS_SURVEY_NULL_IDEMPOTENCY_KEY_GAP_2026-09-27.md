# 147 — customer_success survey responses: NULL idempotency_key defeats dedup entirely (documented, not fixed — same class as report 87)

**Ephemeral, disposable Postgres container only (`sweep-pg18`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope

`app/modules/customer_success/service.py::record_survey_response()` — the write path behind the live, mounted `POST /customer-success/surveys` endpoint (`app/modules/customer_success/router.py`). Checked as part of the ongoing sweep of recently-added `app/modules/*` files (report 103 added this module).

## 2. Everything else in this file checks out clean

- **GUC pinning**: the router uses `Depends(get_db_session)`, the codebase's standard per-request DI chain (GUC-pinned via the tenant-context middleware ContextVar, already established correct dozens of times this session) — not re-verified in isolation, out of scope.
- **Field mapping**: every column the service inserts/selects (`id`, `tenant_id`, `company_id`, `survey_type`, `score`, `comment`, `source`, `recorded_at`, `idempotency_key`, `created_at`) matches `app/alembic/versions/b1c2d3e4f5a6_customer_survey_responses.py`'s real schema exactly, including both `CheckConstraint`s (`survey_type IN ('nps','csat')`, score-scale-by-type) and the `UniqueConstraint("tenant_id", "company_id", "idempotency_key", ...)` the `ON CONFLICT` clause targets.
- **Type safety**: `SELECT id FROM companies WHERE id::text = :company_id AND tenant_id::text = :tenant_id` correctly casts both sides to text, avoiding the uuid/varchar mismatch bug class found repeatedly elsewhere this session (reports 71/72/74/85/142/143).
- **Honesty**: `survey_summary()`'s `"response_rate": None, "response_rate_reason": "Survey invitations are not yet recorded."` — confirmed no fabricated response rate, matching report 103's own claim.

## 3. The one real finding — NULL `idempotency_key` defeats the `ON CONFLICT` dedup entirely

`idempotency_key` is a **nullable** column (`sa.Column("idempotency_key", sa.String(128), nullable=True)`), and Postgres treats every `NULL` as distinct under a unique constraint — so `ON CONFLICT (tenant_id, company_id, idempotency_key) DO NOTHING` provides **zero deduplication** whenever the key is `NULL`. The API's own contract allows this: `SurveyResponseCreate.idempotency_key: str | None = Field(default=None, ...)`.

**Reproduced directly** against a fresh, disposable, fully-migrated Postgres container: two calls to `record_survey_response()` with identical `(tenant_id, company_id, survey_type="nps", score=9, idempotency_key=None)` — simulating a genuine retry of the same submission — produced **two distinct rows** (`0459742b-...` and `679967fc-...`), confirmed via a direct `SELECT count(*)` returning `2`, not `1`.

## 4. Why documented, not fixed — same reasoning as report 87

The one live frontend caller (`src/app/v3/cs/page.tsx:74`) sends `idempotency_key: typeof crypto !== "undefined" ? crypto.randomUUID() : undefined` — a real UUID in every realistic modern-browser environment, with `undefined` (→ `NULL` server-side) only in the essentially-unreachable case `crypto` itself is unavailable. This is a narrower exposure than report 87's finding, but the same underlying product-semantics ambiguity applies: should the API *require* the key (forcing every caller, including this narrow browser edge case, to supply one), or is a duplicate row on that rare retry an acceptable outcome for a survey response (arguably less harmful than for a billable action-outcome, since a duplicate NPS/CSAT entry mostly just double-counts one respondent in aggregate stats, not a financial/workflow action)? This is a deliberate product decision, not a bug this session should resolve unilaterally — matching the established practice for genuinely ambiguous cases (reports 59/60/84/87).

## 5. Scope and safety

- No files changed — documented only, per the established precedent.
- One disposable, ephemeral Postgres container (`sweep-pg18`) used for reproduction; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Systematic repo-wide sweep — confirmed as the only 2 occurrences of this bug class

Extracted every `INSERT ... ON CONFLICT (...)` clause in the non-test source tree (`app/`, `domains/`, `runtime/`, `intelligence/`, `sdk/`) — 26 distinct call sites across 20 tables. For every multi-column conflict target (single-column `ON CONFLICT (id)` targets are inherently safe, since a primary key is always `NOT NULL`), queried `information_schema.columns` on the fresh, fully-migrated disposable container to check the real nullability of every target column:

| Table | Conflict target columns | All `NOT NULL`? |
|---|---|---|
| `agent_evidence` | tenant_id, company_name, source_url, evidence_type | Yes |
| `company_signals` | tenant_id, company_id, signal_type | Yes |
| `md_entity_matches` | source_a_id, source_b_id | Yes |
| `md_source_rows` (×3 call sites) | source_id, source_record_id | Yes |
| `md_identity_classifications` | global_entity_id, classification_version | Yes |
| `md_review_candidates` | global_entity_id, candidate_type, reason | Yes |
| `md_industry_normalization` | global_entity_id, raw_industry, normalization_method | Yes |
| `md_quality_score_history` | global_entity_id, calc_version | Yes |
| `md_sales_readiness_history` | global_entity_id, calc_version | Yes |
| `md_contact_relationships` | person_global_id, company_global_id, linking_basis | Yes |
| `md_legacy_id_mappings` | legacy_id_type, legacy_id | Yes |
| `md_review_queue_state` | queue_type, subject_key | Yes |
| `tenant_ai_memory_conversations` | tenant_id, conversation_id | Yes |
| `company_features` (×2 call sites) | tenant_id, company_id, feature_name | Yes |
| `intelligence/account_evidence.py`'s `(tenant_id, idempotency_key)` | — | **Different shape, also safe**: this `idempotency_key` is deterministically *derived* (`f"{RULE_VERSION}:{digest}"`), never caller-supplied, so it can never be `NULL` regardless of the column's own nullability. |
| `action_outcomes` (report 87) | tenant_id, action_id, **idempotency_key (nullable)** | **No — confirmed bug** |
| `customer_survey_responses` (this report) | tenant_id, company_id, **idempotency_key (nullable)** | **No — confirmed bug** |

**Result: exactly the 2 already-found occurrences exist in the entire non-test source tree.** Every other `ON CONFLICT` clause has a fully `NOT NULL` conflict target and is not exposed to this bug class. This sweep is conclusive, not a lead for later — no further occurrences to check.

## 7. Scope and safety (continued)

Both nullability checks above ran against the same disposable, ephemeral container as the reproduction in §3; no `salesos_test` or production contact.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the "NULL idempotency key defeats `ON CONFLICT` dedup" bug class as a systematically-verified, complete finding (2 occurrences, both documented not fixed pending a product decision — reports 87 and this one). Next: pivot to a fresh methodology, since the three prior systematic passes (SQL EXPLAIN sweep, RLS/GUC census, mypy triage) and now this fourth targeted sweep have each independently reached a conclusive, saturated result.
