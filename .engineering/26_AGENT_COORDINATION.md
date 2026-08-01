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

# 26 â€” AGENT COORDINATION

> Operating protocol for parallel agents in this repository. Complements DEC-107 (keep parallel ready agents busy) and `21`/`22` (live state/locks).

## 1. Ground rules

| # | Rule |
|---|---|
| 1 | Check `21_RUNTIME_STATE.json` + `22_FILE_LOCKS.json` before ANY write. |
| 2 | One agent owns a path at a time. Shared paths are serialized via locks. |
| 3 | Do not conflict: `TenantList`/security endpoints are parallel-agent-owned (AGENTS.md Â§7) â€” leave alone unless assigned. |
| 4 | Claim work by updating `21` (active_agents / locked_files) before starting. |
| 5 | Release locks on completion; update `02`/`30` with outcomes. |
| 6 | If you discover a discrepancy: record in `02` + `18`; do NOT silently fix. |

## 2. Parallel clusters (see `31` Â§2)

- C1: backend domains / FE features / Ops CI.
- C2: decision backend / capability registry sync.
- C3: workflow runtime / entity resolution.
These have disjoint file sets and can run concurrently.

## 3. Contention points (serialize)

- `app/boot/routers.py`, `app/database.py` â€” high blast-radius; one agent at a time.
- `sdk/capability_registry.py`, `runtime/capability_framework/` â€” shared.
- `docs/CAPABILITY_CATALOG.md`, `docs/adr/`, ADR index â€” Human-owned; agents report only.

## 4. Handshake

- Start: read `10` â†’ `11` â†’ `00` â†’ `21`/`22`.
- Mid: update `21` on state change (locks, blocks, progress).
- End: report files changed + commands + validation label; release locks; update `18`/`30` as needed.

## 5. Conflict resolution

1. If docs disagree â†’ prefer executable evidence + ga-engineering-audit.
2. If `PROJECT_BIBLE.md` scores conflict with audit â†’ audit wins.
3. Parallel agents own `TenantList`/security endpoints â€” leave those files alone unless assigned.

## 6. When this file changes

- On protocol change. Mirror `00`, `25`, `31`, `21`, `22`.
