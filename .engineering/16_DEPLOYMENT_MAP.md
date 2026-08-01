---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 16 â€” DEPLOYMENT MAP

> Every deploy target and its config. **Deployments are frozen at production no-go â€” nothing here is a license to deploy.**

## 1. Targets

| Target | Config | Method | Status |
|---|---|---|---|
| Local dev (Docker) | `salesos/docker-compose*.yml` (7 compose files) | docker compose | usable; host Poetry broken on Windows |
| Staging | `salesos/infra/staging/`, `deploy-staging.yml` | CI deploy | BLOCKED (CI-09) |
| Railway | root `Dockerfile.railway` + `railway.json`, `salesos/railway.json` | railway deploy | credentials gitignored |
| Kubernetes (prod intent) | `salesos/infra/k8s/` (37 files) | K8s manifests + configmaps | production no-go (frozen) |
| VPS | deploy workflows | SSH | BLOCKED (CI-09) |

## 2. Compose stacks (salesos/, 7 files)

Backend (api/worker/beat), postgres, redis, meilisearch, neo4j (optional), kafka (optional), monitoring (prometheus/grafana). Default event bus `in_memory` (degraded).

## 3. K8s (salesos/infra/k8s/, 37 files)

Manifests for backend, frontend, kafka, redis, monitoring + configmaps (K8s configmap expects kafka bus â†’ split-brain vs compose).

## 4. Terraform (salesos/infra/terraform/, 3 files)

IaC for provisioning (envs unspecified â€” treat as ground truth pending verification).

## 5. Monitoring (salesos/infra/monitoring/, 21 files)

Prometheus + Grafana config; `prometheus-token` is ðŸ”’.

## 6. Deploy blockers (live)

- CI-08 GHCR 403 â†’ image push blocked.
- CI-09 VPS/SSH secrets â†’ remote deploy blocked.
- Production no-go â†’ no GA deploy regardless of infra.

## 7. When this file changes

- On infra change, new target, or deploy config change. Mirror `12` (CI), `30` (report), `21` (blockers).
