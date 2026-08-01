# DEC-121 — DB-05 Slice 2: emails/meetings type authority (UUID)

> **Status:** **Accepted** — Slice 2 **CLOSED** (type authority); DB-05 program remains **OPEN**  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20  
> **Authority:** DEC-111 Slice 0 inventory P1 · DEC-113 Slice 1 CREATE · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** ENABLE RLS on deferred-8 · production migrate · Prisma · Railway / APP_POSTGRES (DEC-120) · companies/index/nullable Slice 3 · ALTER UUID→VARCHAR

---

## 1. Decision

**Alembic / live DDL wins.** Align ORM `MeetingModel` / `EmailModel` to PostgreSQL `UUID` for `id`, `tenant_id`, and `opportunity_id`. Do **not** ALTER the database to `String(36)`.

| Pin | Value |
|---|---|
| Authority | Migration `0013_meetings_emails.py` (`sa.UUID()`) + live `\d emails` / `\d meetings` |
| ORM fix | `UUID(as_uuid=False)` + `Mapped[str]` (domain/repos stay `str`) |
| Alembic head | **`b7e2f65a3f07`** unchanged (model-only; no new revision) |
| Row risk (local Docker) | `emails`/`meetings` **0** rows; no destructive ALTER |
| RLS | Existing `tenant_id::text = current_setting(...)` policies unchanged |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

### Evidence

| Source | Finding |
|---|---|
| Alembic `0013` | `id` / `tenant_id` / `opportunity_id` = `sa.UUID()` |
| Live Docker DB @ tip | same columns = `uuid`; `commercial_opportunities.id` = `character varying` |
| Platform identity | `tenants.id` / `companies.id` / `users.tenant_id` = `uuid` |
| ORM (pre-fix) | `String(36)` — DEC-111 P1 drift |

### Alternatives rejected

| Option | Why rejected |
|---|---|
| DDL → `VARCHAR(36)` to match commercial String cluster | Invasive ALTER; fights `tenants`/`companies` UUID identity; unnecessary with 0 local rows and RLS `::text` casts |
| `UUID(as_uuid=True)` / `Mapped[uuid.UUID]` | Cascades into domain dataclasses + repos; larger blast radius |
| STOP / analysis-only | Fix is additive ORM-only; safe |

---

## 2. Residual (not this land)

- `opportunity_id` UUID vs `commercial_opportunities.id` VARCHAR — no FK today (`0019` deferred); triage with Slice 3+ commercial type/FK work.  
- Broader commercial `String(36)` vs platform UUID identity remains systemic R-20 (outside emails/meetings).  
- Slice 3: index rename + nullable/type triage.  
- Slice 4+: governed ENABLE RLS for deferred-8 (not Category B).

---

## 3. Validation

| Check | Result |
|---|---|
| Docker `alembic heads` | `b7e2f65a3f07` single head |
| Narrow unit tests | Docker `pytest` **32 passed** (`test_emails_meetings_uuid_authority` + `test_meeting_email_repos` + DEC-085 guard) |
| Production `alembic upgrade` | **Not run** |
| Full `alembic check` | **Not re-run** this land |
| Label | **build validated** (narrow Docker pytest) |

**Production GO not claimed. CI GREEN not met. R-14 GO not claimed.**

---

## 4. Records

- Board DB-05 → Slice 2 COMPLETE; next Slice 3.  
- `EXECUTION_DAG.md` / `RISK_REGISTER.md` R-20 next-action.  
- `DECISION_LOG.md` DEC-121.
