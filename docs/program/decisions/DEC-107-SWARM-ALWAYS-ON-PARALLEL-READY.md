# DEC-107 — Swarm always-on parallel READY dispatch (no idle on GHCR/ops)

> **Status:** **Accepted** — orchestrator policy (docs only)  
> **Date:** 2026-08-01  
> **Board:** Program / Engineering Swarm (SalesOS)  
> **Story / risk:** Cross-cutting (CI-08 / CI-09 ops BLOCKED; R-17)  
> **Authority:** Engineering Swarm concurrency diagnosis (canvas + parent transcript evidence, 2026-08-01) · `EXECUTION_DAG.md` READY/PARALLEL · **DEC-104** honesty labels  
> **Out of scope this land:** changing GHA `concurrency` / `needs` · inventing GHCR credentials · softening Stage 6 push · claiming **CI GREEN (full incl. publish)** · overlapping large edits on CI-14/CI-22 board cells

---

## 1. Problem (evidence)

| Fact | Evidence |
|---|---|
| No repo `max_agents` cap | Diagnosis: under-utilization is behavioral, not a configured concurrency ceiling |
| Orchestrator serial CI burn + Multitask "no further action" after GHCR | Parent swarm ~234 min READY-idle while DAG still listed independent PARALLEL tracks |
| CI-08 / CI-09 are **ops BLOCKED leaves** | DEC-104 Option A pending; Stage 6 **build** proven / **push** 403; VPS secrets = CI-09 |
| GHA concurrency cancel-in-progress on `ci-<ref>` | Throughput tax on rapid successive pushes — **note only**; do **not** change workflow in this DEC |

**Inference:** Pausing the whole swarm because GHCR/VPS is BLOCKED wastes READY capacity. Waiting on a named CI field/ops gate must **not** serialize or idle independent ownership areas.

**Numbering note:** This swarm policy is **DEC-107**. CI-14 executive AC close is **DEC-108**.

---

## 2. Decision

1. **Always-on parallel READY:** While any agent waits on CI field evidence or ops (GHCR, VPS/SSH, human Packages write), keep **>=2-3** background Tasks busy on **EXECUTION_DAG PARALLEL / READY** tracks with **independent ownership** (disjoint files / no shared gate ownership). Prefer **>=3** when Multitask capacity allows.
2. **Never pause swarm solely for CI-08 / CI-09:** Treat GHCR and VPS secret provisioning as **BLOCKED leaves**, not a swarm-wide pause. Continue READY work under DEC-104 dual honesty labels.
3. **Prefer ownership areas over serial GHA mirroring:** Dispatch CI-22, DB-05, Category B RLS planning, contract-test expansion, and similar DAG PARALLEL items — **do not** idle the swarm mirroring Stage `needs:` order once those stages are already launched or ops-blocked. (CI-14 CLOSED under DEC-108 — do not reopen for silent Jest 30.)
4. **Honesty (DEC-104 Option D):** Report **CI GREEN (code path)** vs **CI GREEN (full incl. publish)** separately. Do **not** claim full publish GREEN while CI-08 remains BLOCKED.
5. **GHA concurrency:** Record that cancel-in-progress on `ci-<ref>` is a throughput tax. **Do not** change the workflow in this land unless a follow-on DEC proves a safe revision.

---

## 3. Dispatch heuristics (orchestrators)

| Do | Don't |
|---|---|
| Keep >=2-3 PARALLEL READY agents working while CI/ops waits | Stop all Tasks because Stage 6 push 403'd |
| Pick disjoint board ownership (FastAPI cascade / schema / planning / contracts) | Stack agents on the same board cell or shared hot files |
| Append Progress crumbs carefully; avoid rewriting long CI-22 cells mid-flight | Claim whole-pipeline GREEN from Stages 1-5 alone |
| Use DEC-104 labels in status reports | Soften GHCR push / invent tokens / `continue-on-error` without a separate DEC |

---

## 4. Validation

| Check | Result |
|---|---|
| Workflow / secrets / credentials changed | **None** |
| Pipeline re-run for this DEC | **Not run** |
| Label | **docs only / not validated** (pipeline) |

**CI GREEN (full incl. publish):** not met.  
**CI GREEN (code path):** not claimed as a closed program gate by this DEC.
