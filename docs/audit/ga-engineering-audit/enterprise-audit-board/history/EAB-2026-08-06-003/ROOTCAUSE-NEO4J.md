# ROOT-CAUSE FINDING — Production Neo4j OFFLINE + Repair

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-07 · **Mode:** INVESTIGATE (read-only) → REPAIR (user-approved mutation)

---

## 1. Symptom

- Production `/health` reported `graph=unavailable` since before 2026-08-06; staging reported `graph=connected`.
- This was **inverted availability**: staging Neo4j up, production Neo4j down — so any "graph passes" staging soak would validate the *wrong* subsystem for prod.

## 2. Investigation evidence (all read-only)

| Fact | Value |
|------|-------|
| `neo4j-prod` service ID | `2e84ce72-6381-42c1-85dd-7169449e3582` |
| Active deployments before fix | **0** |
| All historical deployments | **REMOVED** (since 2026-07-29) |
| Image | `neo4j:5-community` |
| Volume attached (prod) | **none** (`neo4j-volume` only exists for staging) |
| App credentials vs service `NEO4J_AUTH` | hash match verified |
| `railway redeploy` result | **"No deployment found for service"** (fails when no active deployment exists) |

**Root cause:** the production `neo4j-prod` service had **zero active deployments** (all removed 2026-07-29) and **no attached volume** in production. `railway redeploy` cannot restart a service with no deployment to restart, so the standard toolpath was unusable.

## 3. Repair (user-approved 2026-08-07)

Used GraphQL mutation `deploymentRedeploy` on the last known deployment record:

- Redeployed deployment ID: `6163f9e3-6b43-4bc6-a9db-0ecdd9fc0154`
- New deployment: `a11ca6f0-96e2-4ed4-9e59-4b2660217671` — **status SUCCESS**
- Logs: `Bolt enabled on 0.0.0.0:7687` · `Started.`
- `neo4j-prod` service: **Online**
- Prod `/health`: `graph=connected`

## 4. Remaining risk (documented, not closed)

- **No volume attached to prod `neo4j-prod`** → data is ephemeral; a redeploy/restart can lose graph data. Parity with staging (`neo4j-volume`) is NOT restored. This is a **P1** needing a human decision (attach `neo4j-volume`-equivalent or accept ephemeral graph for now).
- No runbook captured the GraphQL `deploymentRedeploy` path; `railway redeploy` fails on services with no active deployment.

## 5. Action items (human)

1. Decide whether prod Neo4j needs a persistent volume (recommend: yes, match staging) and attach one.
2. Add a runbook note: if `railway redeploy` says "No deployment found", use `deploymentRedeploy(id: <lastDeploymentId>)` via GraphQL.
