# DEC-130g — DB-05 Slice 5g: residual index / FK / comment / type noise → `alembic check` exit 0

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 VERIFIED/CLOSED** via DEC-130h (Arch PASS + Validation PASS @ `250bcb5`)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130f Slice 5f · DEC-129 KEEP · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP live indexes/tables · dedicated DROP DEC · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN

---

## 1. Decision

Ship **Slice 5g** = maximal honest metadata register for residual live indexes / FKs / comments / types after Slice 5f, plus narrow `include_object` KEEP for one expression GIN that cannot be mirrored without DROP+CREATE. **No blind DROP.** Live Docker `alembic check` **exit 0**. Criterion **7.6 CLOSED** via DEC-130h after Architecture + Validation PASS.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **unchanged** — **`a4f7c29e1b80`** (no new revision) |
| `alembic check` | **exit 0** — `No new upgrade operations detected` |
| True DROP DEC | **0** |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **CLOSED** (DEC-130h) |

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

**Production GO not claimed. CI GREEN not met. Criterion 7.6 CLOSED via DEC-130h** after Architecture + Validation PASS.

---

## 5. Records

- Phase 0 criterion **7.6** → **VERIFIED/CLOSED** (DEC-130h)
- Board DB-05 → **COMPLETE**
- `DECISION_LOG.md` DEC-130g + DEC-130h
- R-20 → Closed — mitigating residual KEEP (`ix_graph_nodes_search`)
- **Not claimed:** Production GO · CI GREEN

---

## 6. Architecture next?

Closed. Residual expression GIN KEEP stands (non-blocking). Next PARALLEL READY clusters: ADR Drift / Capability Drift / EOS / contract tests — do **not** claim Phase 0 GO.
