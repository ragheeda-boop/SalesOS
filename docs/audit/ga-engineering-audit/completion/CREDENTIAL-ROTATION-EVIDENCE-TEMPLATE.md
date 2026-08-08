# Credential Rotation — Field Evidence Template

**Companion runbook:** [CREDENTIAL_ROTATION_RUNBOOK.md](../../ops/CREDENTIAL_ROTATION_RUNBOOK.md) (PREPARED)  
**Gate:** HUMAN-GATE-CARD HG-06 · PROGRAM-BOARD **CP-REL-10**  
**Rule:** **No secrets, tokens, passwords, or private keys in git.** Record hashes/ids/timestamps only.

Copy this file to an out-of-band log **or** fill a redacted copy under:

`completion/evidence/wave-YYYYMMDD-n/cred-rotation/execution-YYYYMMDD.md`

---

## Header (human)

| Field | Value |
|-------|--------|
| Environment | staging / production (circle one) |
| Operator | |
| Date UTC start | |
| Date UTC end | |
| Maintenance window ticket | |
| Runbook revision used | CREDENTIAL_ROTATION_RUNBOOK.md @ \<commit or date\> |

---

## Pre-checks (tick)

- [ ] Stakeholders notified ≥24h (routine) or incident declared (emergency)
- [ ] Env backup taken **off-git** (path recorded privately)
- [ ] Staging exercised before production (if prod)
- [ ] Rollback path rehearsed (restore backup env + restart)
- [ ] Monitoring open (health + auth login probe)

---

## Rotation log (redacted)

| Secret id (name only) | Tier | Action | New material fingerprint | Services restarted | Health after | Notes |
|-----------------------|------|--------|--------------------------|--------------------|--------------|-------|
| e.g. `JWT_SECRET_KEY` | 1 | rotated | sha256=ABCD…(8–12) | backend | `/health` 200 | sessions invalidated OK |
| e.g. `NEO4J_PASSWORD` | 2 | rotated | sha256=… | neo4j, backend | graph=connected | |
| e.g. `STRIPE_SECRET_KEY` | 3 | rotated | Stripe key id `rk_…` / `sk_…` **prefix only** | backend | billing probe | |

Fingerprint = first 8–12 hex of SHA-256 of new secret **or** provider key id — **never** the secret itself.

---

## Post-checks (tick)

- [ ] `/health` (and detailed if used) OK
- [ ] Login issues new token (staging/prod as applicable)
- [ ] No secret strings committed (`git status` clean of `.env*`)
- [ ] Old secrets revoked at provider (where applicable)
- [ ] Incident/maintenance closed

---

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Operator | | | PASS / FAIL |
| Reviewer (TL) | | | PASS / FAIL |

**Honesty:** Completing this template on staging does **not** equal Production GO. Field execution remains Human-Gate until signed.

**Validation of blank template:** **not validated** (documentation only).
