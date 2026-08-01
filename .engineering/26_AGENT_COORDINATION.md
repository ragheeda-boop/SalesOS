---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 26 — AGENT COORDINATION

> Operating protocol for parallel agents in this repository. Complements DEC-107 (keep parallel ready agents busy), DEC-145 (criterion 8.2 caps + namespacing), `.ai/` org baseline (ARB-2026-08-01-003), and `21`/`22` (live state/locks).

## 0. Caps + namespacing (DEC-145 / criterion 8.2)

| Cap | Value | Authority |
|-----|-------|-----------|
| Permanent roles max | **4** | `.ai/runtime/runtime-spec.yaml` · ARB freeze |
| Max parallel temporary workers | **8** | `runtime-spec.yaml` → `max_parallel_workers` |
| Min parallel READY (ops wait) | **2** (prefer **3**) | DEC-107 |
| Max agents total | **12** (≤4 + ≤8) | `runtime-spec.yaml` → `max_agents_total` |

**Namespacing (mandatory):** temporary workers use `parent-domain/task` labels only — e.g. `backend/api-worker`, `architecture/adr-worker`, `validation/ci-worker`. Never `Worker-001`. See `.ai/docs/WORKER_EXECUTION.md`.

**Full scheduler runtime** remains DEFERRED (criterion 9.3 / ADR-036). These caps are **Orchestrator policy**, not a running queue.

## 1. Ground rules

| # | Rule |
|---|---|
| 1 | Check `21_RUNTIME_STATE.json` + `22_FILE_LOCKS.json` before ANY write. |
| 2 | One agent owns a path at a time. Shared paths are serialized via locks. |
| 3 | Do not conflict: `TenantList`/security endpoints are parallel-agent-owned (AGENTS.md §7) — leave alone unless assigned. |
| 4 | Claim work by updating `21` (active_agents / locked_files) before starting. |
| 5 | Release locks on completion; update `02`/`30` with outcomes. |
| 6 | If you discover a discrepancy: record in `02` + `18`; do NOT silently fix. |
| 7 | Stay within caps in §0; serialize rather than spawn past `max_parallel_workers`. |

## 2. Parallel clusters (see `31` §2)

- C1: backend domains / FE features / Ops CI.
- C2: decision backend / capability registry sync.
- C3: workflow runtime / entity resolution.
These have disjoint file sets and can run concurrently.

## 3. Contention points (serialize)

- `app/boot/routers.py`, `app/database.py` — high blast-radius; one agent at a time.
- `sdk/capability_registry.py`, `runtime/capability_framework/` — shared.
- `docs/CAPABILITY_CATALOG.md`, `docs/adr/`, ADR index — Human-owned; agents report only.

## 4. Handshake

- Start: read `10` → `11` → `00` → `21`/`22`.
- Mid: update `21` on state change (locks, blocks, progress).
- End: report files changed + commands + validation label; release locks; update `18`/`30` as needed.

## 5. Conflict resolution

1. If docs disagree → prefer executable evidence + ga-engineering-audit.
2. If `PROJECT_BIBLE.md` scores conflict with audit → audit wins.
3. Parallel agents own `TenantList`/security endpoints — leave those files alone unless assigned.
4. Path overlap without a lock → stop; acquire `22_FILE_LOCKS.json` or yield to the lock holder.
5. Cap breach → Orchestrator serializes; do not invent permanent roles.

## 6. Related AI Organization (`.ai/`)

| Need | Path |
|------|------|
| Role contracts (4 permanent) | `.ai/roles/` |
| Engine bindings | `.ai/runtime/agent-bindings.yaml` |
| Caps + parallel policy | `.ai/runtime/runtime-spec.yaml` · `.ai/docs/PARALLEL_EXECUTION.md` |
| Worker naming | `.ai/docs/WORKER_EXECUTION.md` |
| Criterion cycle | `.ai/docs/EXECUTION_LIFECYCLE.md` |

## 7. When this file changes

- On protocol change. Mirror `00`, `25`, `31`, `21`, `22`, and `.ai/runtime/runtime-spec.yaml` when caps move.
