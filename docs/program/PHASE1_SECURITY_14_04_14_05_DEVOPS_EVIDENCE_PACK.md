# DevOps evidence pack — Security STORY-14-04 / 14-05 support

> **Audience:** Security (pentest 14-04 + SOC2 Type I evidence 14-05)  
> **Tip pin:** `4754b8b` (docs close) / deploy harden `654b33e` / Health Gate land `c0e4f6a`  
> **Honesty:** Not Production GO. Stage 6 GHCR remains **SKIPPED** (DEC-150 B). Live prod kill not performed.

## Deploy / CI tip-line (absolute tip `4754b8b`)

| Workflow | Conclusion | URL |
|----------|------------|-----|
| CI (Stages 1–5) | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457682 |
| Deploy Production | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457753 |
| Docker Smoke | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457157 |
| Security Scan | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835461517 |

### Stage 6 GHCR (quarantined)

From CI run `30835457682` @ `4754b8b`:

- `Stage 6: Build Backend (QUARANTINED DEC-150 B)` → **skipped**
- `Stage 6: Build Frontend (QUARANTINED DEC-150 B)` → **skipped**

Do **not** reopen GHCR as a mandatory gate for 14-04/14-05 packs.

## Backend Health Gate proof (stale-image reject)

| Item | Evidence |
|------|----------|
| Gate definition | `.github/workflows/deploy.yml` job `Backend Health Gate` |
| Requirements | `/health` 200 + `uptime_seconds` &lt; 900 + `GET /api/v1/load/meta` ≠ 404 |
| Landed | `c0e4f6a` — `ci(deploy): wait for Railway roll; reject stale /health false-green` |
| Tip-line proof @ `4754b8b` | Deploy job **Backend Health Gate** = **success** on https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457753 |
| Log-stream false-RED close | `654b33e` — newest-deployment SUCCESS poll; Deploy https://github.com/ragheeda-boop/SalesOS/actions/runs/30834619512 |

## Railway published target (non-prod single-env DEC-149)

- Base URL: `https://salesos-production-96c0.up.railway.app`
- Health: `GET /health` (db connected; kafka=`in_memory`)
- Tip fingerprint: `GET /api/v1/load/meta` → 401 unauth / 200 with Bearer (404 = stale/wrong service)

## STORY-14-01 related (context only — not Security acceptance)

- Field HTTP tip path phases 1–5: **light/build validated** (harness exit 0)
- Real 2h soak: **optional** Board residual (not required for BE close); see field soak script + evidence under `.tmp-1401-field-soak/` when run
- Companion mode ≠ acceptance

## What Security can reuse

1. CI SUCCESS + Security Scan SUCCESS URLs above (change-management / pipeline evidence)  
2. Deploy + Health Gate SUCCESS (change deploy + runtime tip-live control)  
3. Explicit Stage 6 SKIPPED note (DEC-150 B) — do not treat GHCR absence as unexplained gap  
4. No Production GO claim in any of these packs  
5. **AI honesty (AI-Lead support):** cite [`AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md) + 14-05 crumb AI honesty index — `feature_ai_copilot=False`, Decision package **STUB**, no live LLM GO. Non-prod harness crumbs: [`PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](./PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md), [`PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md`](./PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md)

## Forbidden

- Claiming Production GO / GA GO from this pack  
- Reopening Stage 6 GHCR as mandatory  
- Inventing pentest or SOC2 Type I audit completion  
- Marketing live LLM / copilot GA / Decision STUB as production AI from this pack
