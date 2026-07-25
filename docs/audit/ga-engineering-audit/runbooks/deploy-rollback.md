# Deploy / Rollback Runbook (Wave 12 — PREPARE)

**ID:** PROD-W12-001 / PROD-W12-002  
**Status:** PREPARE ONLY — production cutover **not executed**  
**Classification:** Operational prep; does **not** grant Production GO  
**Scoreboard:** [../GA_STATUS.md](../GA_STATUS.md) — **NO-GO**  
**Wave 12 progress:** [../PROGRESS-WAVE12-GATES.md](../PROGRESS-WAVE12-GATES.md)  
**Related:** `salesos/.github/workflows/deploy-production.yml`, `salesos/infra/k8s/DEPLOYMENT_RUNBOOK.md`, `salesos/docs/ONCALL_RUNBOOK.md`

---

## Evidence: what is DONE vs still OPEN

| Item | Status | Evidence |
|------|--------|----------|
| Rolling deploy model documented | **DONE** (docs) | This runbook; `deploy-production.yml` |
| Rollback protocol documented | **DONE** (docs) | This runbook; ONCALL |
| Pre-deploy gate script | **DONE** | `salesos/scripts/pre-deploy-gates.ps1` |
| `jsonschema` declared for image | **DONE** (pyproject) | `salesos/backend/pyproject.toml`; until rebuild: `pip install 'jsonschema>=4.22'` in container — [PROGRESS-WAVE12-GATES.md](../PROGRESS-WAVE12-GATES.md) |
| FE build green | **DONE** (local) | [PROGRESS-WAVE0-FE.md](../PROGRESS-WAVE0-FE.md) |
| FE image route smoke | **DONE** (local) | [PROGRESS-WAVE4-FE-IMAGE.md](../PROGRESS-WAVE4-FE-IMAGE.md) |
| Alembic local head + check script | **DONE** (local) | [PROGRESS-WAVE1-3-5-PLATFORM.md](../PROGRESS-WAVE1-3-5-PLATFORM.md) |
| Security P0 code fixes | **DONE** (light) | [PROGRESS-WAVE2-SEC.md](../PROGRESS-WAVE2-SEC.md) |
| Unit suite local green-ish | **DONE** (Docker) | [PROGRESS-CONTINUATION.md](../PROGRESS-CONTINUATION.md) |
| Infra/obs/secrets config | **DONE** (config) | [PROGRESS-WAVE4-8-9-INFRA.md](../PROGRESS-WAVE4-8-9-INFRA.md) |
| Docs / AI honesty | **DONE** | [PROGRESS-WAVE6-7-DOCS.md](../PROGRESS-WAVE6-7-DOCS.md) |
| Staging soak (Wave 11) | **PARTIAL** | Short local loop evidence — [../PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md); 48–72h / cloud **OPEN** |
| Backup/restore drill (Wave 10) | **DONE** (local) | [../PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md); WAL/PITR **OPEN** |
| Local deploy + rollback tabletop | **DONE** (local) | [../PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md) |
| Staging (cloud) deploy + rollback tabletop | **BLOCKED** (prep **DONE**) | No credentials yet — [../PROGRESS-WAVE12-STAGING.md](../PROGRESS-WAVE12-STAGING.md); unblock: [../PROGRESS-WAVE12-STAGING-UNBLOCK.md](../PROGRESS-WAVE12-STAGING-UNBLOCK.md), [staging-fill-in.md](./staging-fill-in.md) |
| Production migrate / cutover | **OPEN** | **Do not execute while NO-GO** |

---

## Default GA deploy model

**Rolling update on Kubernetes** via GitHub Actions (not blue/green as default).

| Step | Evidence |
|------|----------|
| Trigger | Tag `v*.*.*` or `workflow_dispatch` with version |
| Gate | CHANGELOG must contain version; `RELEASE_GATES.md` optional warning |
| Build | Push GHCR `ghcr.io/ragheeda-boop/salesos/{backend,frontend}:${SHA}` |
| Deploy | `kubectl apply -k infra/k8s/` in namespace `salesos` |
| Wait | `kubectl rollout status deployment/backend|frontend --timeout=300s` |
| Smoke | Workflow smoke-tests job against `https://api.salesos.com` / `https://app.salesos.com` |
| Auto rollback job | `rollback-on-failure` sets previous images |

**يحتاج تحقق:** Cluster credentials, DNS, and smoke URLs are live for the real production account.

---

## Pre-deploy gates (must be green before T-0)

### Automated (required)

```powershell
cd salesos
.\scripts\pre-deploy-gates.ps1
# Optional heavy gate:
.\scripts\pre-deploy-gates.ps1 -RunUnitTests
```

Fails closed on:

1. Alembic drift (`python scripts/check_alembic_head.py` via compose exec)  
2. `GET /health` not ok  
3. `SALESOS_TESTING` truthy / trap value on host or in backend container  
4. (Optional) unit pytest non-zero when `-RunUnitTests`

### Manual checklist

1. Waves 0–5 critical items closed per PRODUCTION_PLAN — see evidence table above (prep **DONE** locally; staging/prod proof **OPEN**).  
2. CI green on release commit.  
3. Staging soak accepted (Wave 11) — **OPEN**.  
4. Backup drill report exists (Wave 10) or CTO-signed exception — **OPEN**.  
5. Feature flags honest: `feature_ai_copilot=False` unless explicitly approved.  
6. `DEMO_MODE=false` in production env.  
7. Backend image includes `jsonschema` (rebuild after pyproject change) or documented emergency `pip install` only for non-prod debug.

---

## Deploy commands (reference)

### CI (recommended)

```bash
# From release commit — tag must match CHANGELOG
git tag vX.Y.Z
git push origin vX.Y.Z
# Or: Actions → Deploy to Production → workflow_dispatch
```

**Do not run production deploy while [GA_STATUS.md](../GA_STATUS.md) is NO-GO.**

### Manual K8s (emergency only — UNVERIFIED for your kubecontext)

```bash
export KUBE_NAMESPACE=salesos
cd salesos/infra/k8s
kustomize edit set image ghcr.io/ragheeda-boop/salesos/backend:<SHA>
kustomize edit set image ghcr.io/ragheeda-boop/salesos/frontend:<SHA>
kubectl apply -k ./ --namespace $KUBE_NAMESPACE
kubectl rollout status deployment/backend -n $KUBE_NAMESPACE --timeout=300s
kubectl rollout status deployment/frontend -n $KUBE_NAMESPACE --timeout=300s
```

### Migrations

Prefer migrate **before** opening traffic (PROD-W1-002). Typical pattern:

```bash
# Inside backend pod / job — exact Job manifest يحتاج تحقق
kubectl exec -n salesos deploy/backend -- alembic upgrade head
kubectl exec -n salesos deploy/backend -- alembic current
# Or gate:
kubectl exec -n salesos deploy/backend -- python scripts/check_alembic_head.py
```

**Policy:** Prefer **forward-fix** over Alembic downgrade. Do not schema-downgrade in panic without a data plan.

### Compose (non-prod / staging compose path)

```bash
cd salesos
docker compose up -d --build
.\scripts\pre-deploy-gates.ps1
# Backup profile separate:
docker compose --profile backup run --rm backup backup-db
```

Root `docker-compose.yml` includes observability extras — document which stack is “canonical” for the env (Wave 4/8).

---

## Rollback triggers

Initiate rollback if any of:

| Trigger | Severity |
|---------|----------|
| Smoke fail after deploy | S1 |
| 5xx above alert threshold sustained | S1/S2 per `alerts.yml` |
| Alembic migrate fail before traffic | Abort launch (no DNS open) |
| Pre-deploy gates fail | Abort launch |
| Confirmed tenant IDOR / SSRF / auth P0 regression | S1 + security incident |
| Data corruption indicators | S1 + restore drill path |

---

## Rollback commands

### Preferred (K8s rollout undo)

```bash
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos
kubectl rollout status deployment/backend -n salesos --timeout=300s
kubectl rollout status deployment/frontend -n salesos --timeout=300s
kubectl rollout history deployment/backend -n salesos
```

### Workflow-aligned (set previous image)

As in `deploy-production.yml` `rollback-on-failure` job (`kubectl set image ...`).

### Notify

Per ONCALL: Slack `#salesos-deployments` / `#salesos-critical` — **يحتاج تحقق** channels exist for the org.

---

## Feature-flag kill switches

| Flag | Safe GA default | Kill use |
|------|-----------------|----------|
| `feature_ai_copilot` | False | Keep off if AI errors spike |
| Admin `ai_copilot` | False (seed aligned Wave 6) | Disable via admin API if enabled in lab |
| Marketplace / experimental routes | Out of GA until Wave 4 route parity | Hide nav / flag |

---

## Tabletop (required before trusting this runbook)

- [x] Dry-run: walk deploy + rollback on **local compose** — [../PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md)  
- [ ] Dry-run: walk deploy + rollback on **staging** without blaming production — **BLOCKED** pending credentials; prep DONE ([../PROGRESS-WAVE12-STAGING-UNBLOCK.md](../PROGRESS-WAVE12-STAGING-UNBLOCK.md))  
- [ ] Confirm who can approve `workflow_dispatch` production  
- [ ] Confirm on-call primary/secondary named for T-0  
- [ ] Run `.\scripts\pre-deploy-gates.ps1` against staging and attach log to Wave 12 progress (local script currently has Windows encoding parse error)

**Acceptance of Wave 12:** runbook present + staging tabletop done.  
**This pass:** runbook + gate script + **local** tabletop **DONE**; staging cloud tabletop **BLOCKED** ([PROGRESS-WAVE12-STAGING.md](../PROGRESS-WAVE12-STAGING.md)). Still **NO-GO**.
