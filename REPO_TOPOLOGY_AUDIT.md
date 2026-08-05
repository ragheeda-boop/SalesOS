# SalesOS Repository Topology Audit

**Date:** 2026-08-05
**Scope:** Read-only. No files moved, renamed, or deleted.
**Repo root (git):** `Muhide/` — branch `master`, HEAD `54daec3`

> **Governance update (2026-08-05):** This audit's findings led to [`ADR-100: Repository Canonicalization`](docs/adr/0100-repository-canonicalization.md), which is now the governing decision for repository topology. This document is retained as historical findings, not as a decision record. **Known correction:** the classification table below states `archive/sales-os/` was "a clean archived snapshot." That was incorrect — re-verification during ADR-100 execution (`migration-log/phase-04.md`) found `archive/sales-os/` was empty, identical to the other two archive stubs. It has since been properly populated. The table below is left as originally written rather than silently edited; treat the Phase 04 log as the corrected record for that specific item.

## Headline finding

There is one canonical application, and it is not ambiguous once you look past the clutter: **`Muhide/salesos/`**. Root's own `README.md` says so explicitly ("★ Main platform monorepo"), the Quick Start tells you to `cd salesos` first, and it's the only tree with a real `package.json`/`pyproject.toml`, the freshest timestamps (2026-08-05 21:14 vs everything else at 15:56–15:58), and a working `docker-compose.yml`.

The confusion isn't "which one is real" — it's that a **repo reorganization is mid-flight** (see `migration-log/phase-01.md` through `phase-03.md`, all dated today) and stopped after phase 3 of an unknown total. That leaves half-moved directories, empty destination stubs, and one un-archived duplicate sitting at root. A new developer hits the leftovers, not a genuine ambiguity about the app.

## Classification table

| Path | Class | Why |
|---|---|---|
| `salesos/` | **Canonical** | The actual app: `backend/` (FastAPI, poetry), `frontend/` (Next.js 15, npm workspaces), `infra/` (k8s, terraform, monitoring), `docker-compose.yml`. Confirmed canonical by root README. |
| `.git/`, `README.md`, `Makefile`(none at root)| **Canonical** | Git root. Note: no root-level `Makefile`/`package.json` — all tooling entry points live inside `salesos/`. |
| `engineering-os/` | **External (submodule)** | Declared in `.gitmodules` → `github.com/ragheeda-boop/salesos-engineering-os`. Has its own nested `.git`. Active — root README references it as the governance/agent-registry layer. |
| `.ai/` | **Active — frozen** | Its own README states: *"Architecture Frozen: Do not modify `.ai/` unless the change closes a criterion in `PHASE_0_EXIT_CHECKLIST.md`."* Treat as off-limits without separate authorization. |
| `.engineering/` | **Active — generated** | Auto-generated coordination/observation layer (`EngineeringOS v3`, produced by `.engineering/measure_fingerprint.py`). Explicitly states it "does NOT change repository behavior." Not hand-edited. |
| `packages/` (root) | **Active, in-progress** | New home for scraper tooling, created by today's migration: `packages/scrapers/{balady,najiz,rega,taqeem}`, `packages/data`. `packages/widget-template/` exists but is **empty** — a destination stub whose move hasn't happened yet. |
| `data/` (root) | **Active** | Data pipeline output/inventory for the scrapers (`data/DATA_INVENTORY.md`, `raw/cleaned/normalized/golden` stages). |
| `docs/` (root) | **Active** | Product-level docs — ADRs, audits, roadmap, 1,790 files. Distinct in scope from `salesos/docs/` (166 files, engineering/API-specific). Legitimately two different doc sets, but identical folder name at two levels is a standing source of "which docs do I read" confusion. |
| `migration-log/` | **Active** | Record of the in-progress reorg. Only phases 1–3 exist; no phase says "done." Migration is **incomplete**, not abandoned. |
| `sales-os/` (root) | **Duplicate / Legacy — un-archived** | Byte-identical to `archive/sales-os/` except local artifacts (`.env`, `.env.example`, `.github`, `.gitignore`, `__pycache__`). Unrelated product ("MUHIDE Sales OS – Notion Automation Suite", Python scripts for Notion/Apollo sync) that happens to collide in name with SalesOS. It was archived once but the root copy was never deleted — an incomplete archive step. **Highest-confusion item in the repo**: an AI agent or new hire grepping for "sales-os" / "salesos" will hit both and can't tell which is the product. |
| `archive/sales-os/` | **Archive** | Correct, clean archived snapshot. Fine as-is. |
| `archive/engineering-recovery/` | **Archive — broken (empty)** | Directory exists but contains **zero files**. Root `engineering-recovery/` (9 files, an old incident-recovery log, phases 01–14, unrelated to `migration-log/`) was never actually copied in. Anomaly, not a real duplicate. |
| `archive/engineering-os/` | **Archive — broken (empty)** | Same pattern: empty placeholder, root `engineering-os/` (the submodule) was never copied in. |
| `WidgetTemplate/` (root) | **Active — pending move** | Has real content (README, `.tsx`, tests). Its declared destination, `packages/widget-template/`, already exists but is empty. Not yet a duplicate, but will become a conflicting duplicate if anyone edits either copy before the move completes. |
| `infrastructure/` (root) | **Empty scaffold** | `cloud/`, `observability/`, `scripts/` all exist with **zero files**. Looks like a Phase-2-style "create destination dirs first" stub, possibly intended to eventually absorb `salesos/infra/` (which is fully populated: k8s manifests, terraform, docker, monitoring, staging compose). No migration-log entry documents this move — intent is unconfirmed. |
| `docker-compose.yml` (root) | **Active — but easy to run by mistake** | Not a copy of `salesos/docker-compose.yml`. Its own header says: *"Canonical local/dev stack... Staging/prod: use `salesos/docker-compose.yml` or `salesos/docker-compose.prod.yml`."* So root's compose file is a deliberately lighter dev stack, and `salesos/`'s is the staging/prod-shaped one. Two different files, same filename, at two levels — the README's own Quick Start (`cd salesos && docker compose up`) bypasses the root file entirely, making it easy to wonder which one is "the" way to boot. |
| `railway.json` + `Dockerfile.railway` (root) | **Conflicting duplicate** | Root version builds backend-only via `Dockerfile.railway` (which `COPY`s from `salesos/backend/...`). `salesos/railway.json` builds via `salesos/backend/Dockerfile` directly and additionally handles `celery-worker`/`celery-beat` service variants and a `preDeployCommand: alembic upgrade head`. These are materially different deploy configs for the same target — whichever one Railway is actually pointed at should become the single source of truth; the other is dead config risk. |
| Root loose report/deck files (`SALESOS_*.md` ×7, `PRODUCT_BIBLE.md`, `RUNBOOK.md`, `muhide_*_report.md` ×3, `*.pptx` ×4, `*.zip` ×2) | **Clutter, not duplicates** | Point-in-time audit/roadmap snapshots and design decks sitting loose at repo root. `docs/audit/` already exists at root with a clean numbered structure (`00-salesos-knowledge-base.md` … `09-ai-architecture.md`) — a ready destination. The zip/pptx files total ~35 MB and inflate every clone for no runtime purpose. |

## Confirmed NOT duplicates (despite name collisions)

- `packages/` (root, scraper tooling) vs `salesos/packages/` (frontend/platform workspace packages) — different products, coincidentally same folder name.
- `docs/` (root, product/audit docs) vs `salesos/docs/` (engineering/API docs) — different scope, coincidentally same folder name.
- `infrastructure/` (root, empty) vs `salesos/infra/` (populated) — different name even, not literal dupes; root one just looks like an abandoned scaffold.

## Nested git / submodules

- `.git` — root, canonical.
- `engineering-os/.git` — real submodule, tracked in `.gitmodules`. No other nested `.git` directories found anywhere else in the tree.

## Migration plan (zero-risk — proposal only, nothing executed)

Ordered by risk, lowest first. Each step is independently reversible and none touches `salesos/` internals.

1. **Delete the two broken empty archive stubs**: `archive/engineering-os/`, `archive/engineering-recovery/`. Zero content loss (they're empty) — but confirm first whether the *intent* was to archive `engineering-os/` (a live submodule — archiving it is unusual and worth asking about) and root `engineering-recovery/` (9 files, currently un-archived and still live at root either way).
2. **Resolve `sales-os/` vs `archive/sales-os/`**: diff confirms root copy is superseded. Recommend deleting root `sales-os/` (after user re-confirms nothing depends on it — check for references first) since a clean archived copy already exists. Renaming, not deleting, is the safer first move if there's any doubt.
3. **Decide root `infrastructure/{cloud,observability,scripts}`**: either (a) it's a stale, unused scaffold → delete, or (b) it's an intended future destination for `salesos/infra/` → needs its own migration-log phase before any files move, since `salesos/infra/` is referenced by k8s manifests, terraform state, CI, and docs. Recommend asking before touching.
4. **Finish or shelve the `WidgetTemplate/` → `packages/widget-template/` move**: currently safe (source has content, destination is empty, nothing conflicts), but it's an open half-step from the same migration series. Low risk, purely additive.
5. **Resolve the two `railway.json`/`Dockerfile.railway` pairs**: requires knowing which one Railway's dashboard is actually configured to build from (external, can't be seen from the repo alone) — ask before deleting either.
6. **Clarify the two `docker-compose.yml` files' relationship in the README**: no file changes needed, just make the root README's Quick Start explicit that root's compose file is a separate lighter profile, not an alternate way to boot the same stack.
7. **Relocate loose root-level audit/report markdown and decks into `docs/audit/` or `docs/releases/`**: pure hygiene, no functional risk, but should wait until after the higher-priority items since it's the least urgent.

## What I did not do

No files were moved, renamed, or deleted. No configs were edited. This is audit-only, per your instruction.

## Recommended next step

Confirm items 1–3 and 5 above (the ones needing your call on intent), then I'll execute the approved subset one atomic, reversible step at a time — starting with whichever you approve first.
