# Release Archive — v1.0.0-ga

**Immutable Release Record** — created 2026-08-07 per `RELEASE-GOVERNANCE-DECISION-2026-08-07.md`.

## Rules

- Every file here is an **immutable copy** of its source at deposit time.
- **Never edited after deposit.** If a source doc evolves, this archive does not follow.
- New releases get new directories (`v1.0.1`, …); this directory is frozen at GA.

## Contents

```
evidence/     prod health + detailed + auth/RBAC audit + WAL/PITR reverify JSONs (immutable)
governance/   BOARD-CONSENSUS, DOCUMENT-CONTRADICTIONS, AUTHORITATIVE-DOCUMENT-MAP
reports/      OPS01-ROW4-STATUS, CEO-EXECUTIVE-BRIEF-AR, PRODUCTION-AUTH-ROLE-AUDIT
cutover/      PRODUCTION-CUTOVER-PACKAGE, MAINTENANCE-WINDOW-PACKAGE
decisions/    RC-DECISION-PACKET (RC-01…08), RELEASE-GOVERNANCE-DECISION
signatures/   SIGN_HERE, GO-LIVE-SIGNATURE-PACKET
soak/         (populated at soak closure: SOAK-COMPLETION-REPORT + loop evidence index)
```

## Source of truth

- Governance/decisions live and evolve in `docs/audit/ga-engineering-audit/` + `reconciliation-2026-08-07/`.
- This archive is the **frozen snapshot**; consult it to recall the exact release-time state.

## Status

- Release Status: **ACTIVE** (Engineering CLOSED; Change Freeze until 2026-08-10T14:10Z).
- Soak evidence deposited into `soak/` only after official closure.
