# DEC-130g — DB-05 Slice 5g: residual index / FK / comment / type noise → `alembic check` exit 0

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Package = **READY FOR REVIEW** (Architecture / Validation: check-clean honesty + evidence; Orchestrator may CLOSE criterion **7.6** only after Arch+Val PASS)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130f Slice 5f · DEC-129 KEEP · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP live indexes/tables · dedicated DROP DEC · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED without Arch+Val

---

## 1. Decision

Ship **Slice 5g** = maximal honest metadata register for residual live indexes / FKs / comments / types after Slice 5f, plus narrow `include_object` KEEP for one expression GIN that cannot be mirrored without DROP+CREATE. **No blind DROP.** Live Docker `alembic check` **exit 0**. Criterion **7.6** stays formally **OPEN** until Architecture + Validation PASS; package is READY FOR REVIEW for the close path.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **unchanged** — **`a4f7c29e1b80`** (no new revision) |
| `alembic check` | **exit 0** — `No new upgrade operations detected` |
| True DROP DEC | **0** |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** (READY FOR REVIEW — Orchestrator may CLOSE after Arch+Val PASS) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) Blind DROP of rename-twin / expression indexes | **Rejected** — live twins KEEP until dedicated DEC |
| (b) DROP+CREATE `ix_graph_nodes_search` to match ORM expression text | **Rejected** — no blind DROP; Postgres `::regcast` reflection drift |
| (c) Metadata register + twin KEEP + narrow include_object for expression GIN | **Approved** |

---

## 2. Scope (ORM / metadata — no DDL)

### Index register (live names + rename twins)

Commercial / analytics / contacts / DLQ / emails / meetings / ER / golden / google / licenses / notifications / SSO / employee unique / webhooks / marketplace — register live `__table_args__` Index names; keep rename twins (`ix_contracts_tenant_status`, `ix_recommendations_target`, `ix_analytics_report_executions_report_id`, `ix_licenses_company_id`, `ix_sso_connections_user_id`, …).

### FK / comment / unique duals

| Area | Action |
|---|---|
| `golden_records.tenant_id` / `entity_resolution_conflicts.tenant_id` | Add `ForeignKey("tenants.id")` |
| `feature_values.feature_key` | `ondelete="CASCADE"` to match live |
| `webhook_deliveries.subscription_id` | FK CASCADE + `ix_webhook_deliveries_status_retry` |
| companies `cr_*` / `status` comments | Strip ORM comments (DB has none; no COMMENT DDL) |
| `golden_records.data` comment | Align to live text (no `verified_by`) |
| `tenants.slug` / `users.email` | `UniqueConstraint(*_key)` + non-unique `ix_*` (live dual) |
| timeline | Match live expression indexes + `ix_timeline_actor` |
| vectors Core | `postgresql.TEXT` id + `_PgVector` embedding stand-in |

### Expression KEEP (`include_object`)

| Index | Disposition |
|---|---|
| `ix_graph_nodes_search` | **KEEP** — skipped in `app/alembic/env.py` `include_object`; live GIN retained; no DROP |

### Explicit model imports

`database.py` registers communication_hub / employee intelligence / notifications / webhooks / feature_store for metadata coverage.

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
alembic_version: a4f7c29e1b80 (head unchanged)
docker compose exec -T backend alembic check  → exit 0
  "No new upgrade operations detected."
```

| Class | Before (5f @ `a4f7c29e1b80`) | After (5g metadata @ `a4f7c29e1b80`) | Notes |
|---|---:|---:|---|
| `alembic check` exit | **255** FAILED | **0** | clean |
| `Detected removed index` (approx) | **36** | **0** | register + twins + expression KEEP skip |
| FK / comment / type residual ops | present | **0** | ORM align |
| True DROP DEC | 0 | **0** | unchanged |
| DEC-085 `set_config` | intact | intact | untouched |

Log capture (local, not committed): `.tmp-alembic-check-7-6-slice5g-final.txt`

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic_version` / head | `a4f7c29e1b80` |
| Docker `alembic check` | **exit 0** |
| New Alembic revision | **None** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker alembic check exit 0 + residual inventory) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED by this package** — Orchestrator may CLOSE after Architecture + Validation PASS.

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (READY FOR REVIEW / check-clean evidenced; close path unlocked)
- Board DB-05 → Slice 5g COMPLETE; residual = Arch+Val for 7.6 close
- `DECISION_LOG.md` DEC-130g
- R-20 next-action → Arch+Val then Orchestrator CLOSE 7.6 (or residual if Val finds gaps)
- **Not claimed:** Production GO · CI GREEN · 7.6 VERIFIED/CLOSED without Arch+Val

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) metadata register + rename-twin KEEP (no DROP) is sound, (2) `include_object` skip for `ix_graph_nodes_search` is honest KEEP vs DROP+CREATE, (3) dual unique tenants/users match live `*_key` + non-unique `ix_*`, (4) head pin `a4f7c29e1b80` unchanged (no DDL) is correct, (5) Docker `alembic check` exit 0 is sufficient evidence for READY FOR REVIEW toward 7.6 close. Validation: corroborate exit 0 + head pin + DEC-085 intact — do **not** claim Production GO / CI GREEN.
