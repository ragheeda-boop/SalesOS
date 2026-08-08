# Progress — Wave 12 Image Bake (jsonschema)

**Date:** 2026-07-22  
**Scope:** Local SalesOS backend Docker image rebuild only — **no prod deploy**, **no DB wipe**  
**Product:** SalesOS  
**Validation class:** **light validated** (image rebuild + container recreate + import/schema/health probes)  
**Production GO:** **Not claimed** (audit remains **production no-go**)

---

## Summary

| Item | Result |
|------|--------|
| Pre-rebuild `import jsonschema` | **FAIL** — `ModuleNotFoundError` (stale `salesos-backend:latest`) |
| `docker compose build backend` | **PASS** — exit 0 (~35 min) |
| Recreate backend (`--no-deps --force-recreate`) | **PASS** — volumes preserved; Postgres data untouched |
| Baked `jsonschema` | **4.26.0** at `/usr/local/lib/python3.12/site-packages/` |
| `validate_event` (jsonschema path, not fallback) | **PASS** |
| `/health` cache + redis | **connected** |
| Docker health | **healthy** |
| `pre-deploy-gates.ps1` | Initially **parse FAIL** (Unicode) during image bake; **later fixed + runtime PASS** — see [PROGRESS-WAVE12-GATES.md](./PROGRESS-WAVE12-GATES.md) |

---

## Image identity

| Field | Value |
|-------|--------|
| Tag | `salesos-backend:latest` |
| Image ID / digest | `sha256:27ac6fc72b41f8bdc23937d44f39aa46e577e73e1e9d02d142607d4ee99569ed` |
| Short ID | `27ac6fc72b41` |
| Created | 2026-07-22T08:35:15Z |
| Approx size | ~117 MB |
| Compose | `salesos/docker-compose.yml` service `backend` |
| Build context | `salesos/backend` + `Dockerfile` (`pip install .` from Poetry `pyproject.toml`) |

**Dependency source:** `salesos/backend/pyproject.toml` → `jsonschema = "^4.22"` resolved to **4.26.0** during image build (`Collecting jsonschema<5.0,>=4.22`).

---

## Commands run (evidence)

```text
# From salesos/
docker compose build backend
# → Image salesos-backend Built; pip installed jsonschema-4.26.0

docker compose up -d --no-deps --force-recreate backend
# → Container salesos-backend-1 Recreated / Started (no volume prune)

# Pre-rebuild (control)
docker compose exec -T backend python -c "import jsonschema; print(jsonschema.__version__)"
# → ModuleNotFoundError: No module named 'jsonschema'

# Post-rebuild
docker compose exec -T backend python -c "from importlib.metadata import version; import jsonschema; print(version('jsonschema')); print(jsonschema.__file__)"
# → 4.26.0
# → /usr/local/lib/python3.12/site-packages/jsonschema/__init__.py
```

### Schema validation (not fallback-only)

One-liner exercised `sdk.events.schema_registry.validate_event` with missing required fields and a wrong type:

```text
missing_required_errors:
  ["'company_id' is a required property", "'tenant_id' is a required property"]
type_errors:
  ["123 is not of type 'string'"]
```

These match **jsonschema Draft7Validator** message style (e.g. `"123 is not of type 'string'"`). Fallback helper uses slightly different wording (`'tenant_id' is not of type 'string'`). Combined with successful `import jsonschema`, this confirms the primary path — not ImportError → `_validate_event_fallback`.

### Health

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "connected",
  "cache": "connected",
  "graph": "unavailable",
  "kafka": "in_memory",
  "redis": "connected",
  "rate_limiter": "active"
}
```

Docker inspect: `Health=healthy`.

**Note:** Boot log briefly logged `cache: unavailable` / `sdk cache: unavailable` during Phase 1; by the time `/health` was probed after startup complete, both **cache** and **redis** reported **connected**. Graph remains `unavailable` (local Neo4j timing/auth not in scope here). Kafka remains `in_memory` per compose default `EVENT_BUS_TYPE`.

---

## pre-deploy-gates.ps1

Attempted:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pre-deploy-gates.ps1
```

**Result:** ParserError at line 79 — em-dash / Unicode in string (`" — $Detail"`) corrupted under Windows PowerShell 5.1 file encoding. `pwsh` not installed on host. **No gates executed by the script.**

**Mitigation used:** Manual `/health` probe (above) — satisfies the user alternate (“or health check”). Script encoding fix is **out of scope** for this image bake task; track separately if Wave 12 gates must run on Windows PS 5.1.

---

## Constraints honored

- Local only — no staging/prod push  
- No `docker compose down -v` / volume prune — Postgres data retained  
- Alembic at boot (image bake): `current=0039 head=0039` (no migrate forced). **Current repo/DB head is now `0040`** — include in staging/prod upgrade path; see [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md)  
- No secret / `.env` weakening  

---

## Return board (requested)

| Field | Value |
|-------|--------|
| **Image tag** | `salesos-backend:latest` (`27ac6fc72b41` / `sha256:27ac6fc72b41…`) |
| **jsonschema version** | **4.26.0** |
| **Health status** | **ok** — `cache=connected`, `redis=connected`, Docker **healthy** |

---

## Known limitations

- Validation is **light** (import + one-liner + HTTP health) — full unit suite / `pre-deploy-gates.ps1` not green on this host path.  
- FE volume-mount vs image bake: backend bind-mounts `./backend:/app` for source; **site-packages** (including jsonschema) come from the image — rebuild was required and is now current.  
- Does not change Production Readiness / Security scores or NO-GO decision.
