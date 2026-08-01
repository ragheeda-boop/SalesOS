# DEC-074 — CI-19 Wave 3 residual: K8s securityContext + Dockerfile USER + TF encryption

> **Status:** **Accepted** — Wave 3 residual **COMPLETE**; CI-19 remains **OPEN**  
> **Date:** 2026-08-01  
> **Board:** Security / Infra (SalesOS / AQLIYA)  
> **Story / risk:** CI-19 / R-24  
> **Authority:** DEC-043 Wave 1 · DEC-069 Wave 3 SHA-pin · triage `CI_19_SEMGREP_TRIAGE.md`  
> **Out of scope:** Wave 2 SQL honesty · Semgrep gate weaken · Railway · CI-22

---

## 1. Scope (19 alerts)

| Class | Count | Remediation |
|---|---|---|
| K8s `allow-privilege-escalation-no-securitycontext` | **15** | `securityContext.allowPrivilegeEscalation: false` on each container |
| Dockerfile `missing-user` | **2** | `USER postgres` (backup); `USER alertmanager` (alertmanager image) |
| Terraform encryption | **2** | DynamoDB SSE; Secrets Manager CMK + rotation + `kms_key_id` |

App images (backend / frontend / celery / migrate) also set `runAsNonRoot: true` + `capabilities.drop: [ALL]`.

## 2. Architecture STOP (documented)

Data-store pods (postgres / neo4j / kafka / zookeeper / redis) intentionally **omit** `runAsNonRoot` — official images often start as root to fix volume perms then drop. Forcing non-root without UID/`fsGroup` redesign risks broken PVCs. Residual Semgrep rule only required `allowPrivilegeEscalation: false`.

## 3. Decision

Accept Wave 3 residual as **COMPLETE**. Do **not** close CI-19. Do **not** weaken Semgrep. Do **not** execute Wave 2. Next: Wave 4 path excludes or Wave 5 residuals.

## 4. Validation

| Check | Result |
|---|---|
| Manifest inventory vs alert paths | **light validated** |
| Live Code Scanning re-verify | **not validated** (post-push) |
| Semgrep severity / upload | **unchanged** |

**CI GREEN not met.**
