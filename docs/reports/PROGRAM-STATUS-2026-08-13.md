# Program status snapshot — 2026-08-13 (Vercel READY + P1 + FreeLLMAPI shim)

**Classification:** **production no-go** (unchanged; ga-engineering-audit SoT)  
**Product:** SalesOS · Railway backend + Vercel frontend (`sales-os`)  
**Validation honesty:** **light validated** (Vercel Production READY on lint/TS chain; P1 Jest/Docker pytest as cited) + **docs** for residuals  
**AI flag:** `feature_ai_copilot` remains **false** — **not flipped**  
**Prior snapshot:** [`PROGRAM-STATUS-2026-08-12.md`](./PROGRAM-STATUS-2026-08-12.md)

## Closed / PASS this day (agent-closable)

| Track | Status | Evidence |
|-------|--------|----------|
| **Vercel `sales-os` Production** | **READY** on tip `affec87` (lint/TS chain) | Chain `1e642ec` → `be4373d` → `d6d428d` → **`affec87`**. This is Vercel deploy **READY**, **not** GA / Production **GO**, **not** browser pass |
| **P1 U02** workspace navigate | **PASS** (narrow Jest) | SHA `5fff6cb` · [`P1-CLOSURES-2026-08-13.md`](./P1-CLOSURES-2026-08-13.md) |
| **P1 U04** 360 documents / next-steps | **PASS** (narrow Jest) | SHA `8f7ff63` |
| **P1 S10 / C07 / 360 contacts tenant** | **PASS** (narrow Docker pytest + config) | SHA `8296c60` — HSTS `preload`, `images.remotePatterns`, 360 `tenant_id` predicate |
| **P1 360 settings panel** | **PASS** (narrow) | SHA `60a1532` — live company fields; supersedes residual #3 in the 13 Aug P1 closures note |
| **A-09 steps 1–2** CI staging deploy | **PASS** (light) | SHA `550e954` · [31649846410](https://github.com/ragheeda-boop/SalesOS/actions/runs/31649846410) · [`A09-DEPLOY-STAGING-SUCCESS-2026-08-13.md`](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-DEPLOY-STAGING-SUCCESS-2026-08-13.md) |

## FreeLLMAPI — wiring only (not live AI)

| Item | Honest status | SHA / evidence |
|------|---------------|----------------|
| Assessment | Read-only; **not integrated** as a product dependency | [`FREELLMAPI-SALESOS-ASSESSMENT-2026-08-13.md`](./FREELLMAPI-SALESOS-ASSESSMENT-2026-08-13.md) |
| Factory / SDK `openai_base_url` shim | Wired | `110b0c8` |
| App `Settings` inherit on copilot/RAG | Wired | `ad2b227` |
| Remaining `AsyncOpenAI` callers | Wired | `ee5e4bb` |
| `feature_ai_copilot` | **False** (`salesos/backend/app/config.py`) | unchanged |
| Compose sidecar (`--profile freellmapi`) | **unproven** — image pull / health **not validated** | assessment residual §7 |
| Live LLM / copilot GA | **NO** | do not market as live AI |

## Advanced OPEN (not closed)

| Track | Status | Evidence |
|-------|--------|----------|
| **A-09 staging parity** | **CONDITIONAL / OPEN** — PASS 1–6, 8; Human-Gate **7 OPEN**; soak **9 false**; final **10 OPEN** | [`A09_STAGING_PARITY.md`](../audit/star-audit/A09_STAGING_PARITY.md) · rollup [`A09-CHECKLIST-PROGRESS-2026-08-12.md`](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md) |
| **Secrets rotation** | Human **claimed**; runtime **healthy**; SSO browser + provider revoke **not independently verified** | SHA `529b772` · [`HUMAN-SECRET-ROTATION-CHECKLIST.md`](./HUMAN-SECRET-ROTATION-CHECKLIST.md) |
| **OPS-01 / DR gate** | Agent-side **advanced**; CLOSE / PITR / soak **claim still human** | SHA `5badbf4` · [`OPS01-DR-GATE-2026-08-12.md`](./OPS01-DR-GATE-2026-08-12.md) |
| **Vercel AI Gateway key** | **Exposed** — value pasted in chat; **rotate** (human). Do not reuse. | No secret in this file |

### A-09 detail (honest)

- Steps **1–2:** `RAILWAY_TOKEN` accepted; `deploy-staging.yml` **SUCCESS** (`550e954`). Prior Unauthorized rows are historical.
- Step 7 Human-Gate: status matrix + OAuth runbook + rollback template **prep DONE**; ink **OPEN** (OAuth / WAL-PITR-offsite / `max_connections` / rollback tabletop).
- Step 9: `soak_complete_claim=false`; unlock U1–U5 documented — do not flip.
- Step 10: **CONDITIONAL / OPEN** — `staging_parity_complete=false`. Checklist-10 body still shows stale 1–2 BLOCKED; **rollup + STAR A-09 + `550e954` govern** for 1–2.

## Remaining — human vs agent

### Human (do not skip)

1. **Rotate the Vercel AI Gateway key** that was pasted in chat (treat as compromised). Update Vercel Production env; revoke the old key. Do not paste the new value into chat.
2. **A-09 Human-Gate (step 7):** Google OAuth ([staging-oauth-setup.md](../audit/ga-engineering-audit/runbooks/staging-oauth-setup.md)); WAL/PITR/offsite accept-or-enable; `max_connections` 100→500 or signed acceptance; rollback tabletop ([template](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md)).
3. **A-09 soak (step 9):** unlock U1–U5 ([step 9](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md)); do **not** flip `soak_complete_claim`.
4. **SSO browser login + provider revoke** — independently verify (secrets claimed only at `529b772`).
5. **OPS-01 / DR:** ink CLOSE (or DEFER) on DR rows 1–3; enable managed backup + native PITR (or accept residual); TL triage soak failures; signed RPO/RTO acceptance.
6. Do **not** flip `feature_ai_copilot`. Do **not** claim Production **GO**.

### Agent (next, if assigned)

1. MetaData live-table consolidations (DEC-156 **proposal**; freeze ceiling **6**). Residual six Base/KEEP islands still blocked.
2. DUP-01 engine deletion still **deferred** (Partial narrowed).
3. FreeLLMAPI compose sidecar proof (dev profile only) — **optional**; not live AI; not Railway prod.
4. Staging `OPENAI_BASE_URL` loop — **not validated**; do not call live external providers.
5. Leave A-09 Human-Gate / soak claim / GA GO to humans.

## Explicit non-claims

- GA / Production **GO** — **NO** (production **NO-GO**)
- Browser pass / full CI green / full npm lint-build / full pytest — **not claimed**
- Staging parity (STAR A-09) — **not closed** (`staging_parity_complete=false`)
- Wave 11 soak claim — **false**
- OPS-01 DR cutover CLOSED / PITR enabled — **false**
- Live ResearchAgent LLM / FreeLLMAPI **integrated** / `feature_ai_copilot=True` — **NO**
- Compose sidecar health — **unproven**
- MetaData islands fully Fixed / DUP-01 engines deleted — **NO**

**Authority:** executable evidence + [`docs/audit/ga-engineering-audit/`](../audit/ga-engineering-audit/) over superseded vNext GO docs.
