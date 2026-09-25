# DOCUMENT AUTHORITY MODEL — 2026-08-24

**Purpose:** Establish explicit source-of-truth hierarchy. When documents conflict, higher tiers win.

---

## Tier 1 — Runtime Truth (Immutable Reality)

| Source | Location | Authority |
|--------|----------|-----------|
| Source code | `salesos/backend/app/`, `domains/`, `runtime/`, `intelligence/` | HIGHEST — what runs |
| Database migrations | `app/alembic/versions/` | Schema truth |
| Tests | `tests/`, `domains/*/tests/`, `app/modules/*/tests/` | Behavioral truth |
| Configuration | `app/config.py`, `pyproject.toml`, `railway.json` | Runtime config |
| Dockerfiles | `Dockerfile.railway`, `Dockerfile.railway.celery` | Build truth |
| CI/CD | `.github/workflows/` | Pipeline truth |
| Alembic head | `h2i3j4k5l6m8` | Schema truth |

**Rule:** When documentation conflicts with Tier 1, Tier 1 wins. Documentation must be updated.

---

## Tier 2 — Ratified Decisions

| Source | Location | Authority |
|--------|----------|-----------|
| ADRs | `docs/adr/` (28 records) | Architecture decisions |
| AGENTS.md | Root | Agent operating instructions |
| FINAL_GO_NOGO_ASSESSMENT.md | `docs/audit/ga-engineering-audit/` | Current readiness assessment |
| SALESOS_MASTER_CLOSURE_SEQUENCE.md | `docs/audit/ga-engineering-audit/` | Product-closure order |
| AI_HONESTY.md | `docs/audit/ga-engineering-audit/` | AI capability honesty |
| SECURITY_REBASELINE.md | `docs/current-state/` | Fresh security assessment |
| PROJECT_BIBLE.md | `docs/` | Engineering bible |

**Rule:** Tier 2 decisions are binding until superseded by a new Tier 2 decision.

---

## Tier 3 — Current Operating Documentation

| Source | Location | Authority |
|--------|----------|-----------|
| Current roadmap | `docs/roadmap/MASTER_ROADMAP.md` | Active execution plan |
| Current backlog | `docs/roadmap/MASTER_EXECUTION_BACKLOG.md` | Remaining work |
| Current execution sequence | `docs/roadmap/EXECUTION_SEQUENCE.md` | Implementation order |
| Operational runbooks | `docs/ops/` (23 files) | Operational procedures |
| Phase evidence packs | `docs/audit/ga-engineering-audit/PHASE*_EVIDENCE_PACK.md` | Phase validation evidence |
| Wave progress | `docs/audit/ga-engineering-audit/PROGRESS-WAVE*.md` | Wave tracking |

**Rule:** Tier 3 documents are current and actionable. They change as work progresses.

---

## Tier 4 — Historical

| Source | Location | Authority |
|--------|----------|-----------|
| Archived documents | `docs/archive/` | Historical reference only |
| Superseded plans | `docs/vnext/` (archived) | Was once current, now replaced |
| Old audits | `docs/audit/legacy-reports/` | Historical findings |
| Migration log | `migration-log/` | Reorganization record |
| Old UX vision | `docs/v2/` (archived) | Historical design vision |
| Pre-launch analysis | `assets/reports/` | Historical market analysis |

**Rule:** Tier 4 documents are preserved for history. They are NOT authoritative for current decisions.

---

## Conflict Resolution Rules

1. **Tier 1 beats everything.** Code is truth.
2. **Higher tier beats lower tier.** ADR > roadmap > historical.
3. **Same tier: most recent wins.** But must be explicitly superseded.
4. **When uncertain:** Check Tier 1 first, then Tier 2, then ask.
5. **Never silently override.** Document the conflict and resolution.

---

## Document Ownership

| Domain | Owner Document | Location |
|--------|---------------|----------|
| Architecture | ADRs | `docs/adr/` |
| Security | SECURITY_REBASELINE.md | `docs/current-state/` |
| Readiness | READINESS_MATRIX.md | `docs/current-state/` |
| Roadmap | MASTER_ROADMAP.md | `docs/roadmap/` |
| Backlog | MASTER_EXECUTION_BACKLOG.md | `docs/roadmap/` |
| Agent instructions | AGENTS.md | Root |
| Engineering bible | PROJECT_BIBLE.md | `docs/` |
| AI honesty | AI_HONESTY.md | `docs/audit/ga-engineering-audit/` |
| Closure sequence | SALESOS_MASTER_CLOSURE_SEQUENCE.md | `docs/audit/ga-engineering-audit/` |
