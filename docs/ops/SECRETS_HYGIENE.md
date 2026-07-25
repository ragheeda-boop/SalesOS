# Secrets hygiene — SalesOS / AQLIYA (PROD-W9-001 / W9-002)

**Rule:** never commit real secrets. Use `.env` (gitignored) from `.env.example` / `salesos/.env.example`.

## Checklist before T-0

- [ ] Staging and production secrets live in GH Environments / K8s Secrets / ASM only
- [ ] `JWT_SECRET_KEY` and `SECRET_KEY` ≥ 32 chars, distinct per environment
- [ ] `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, `GRAFANA_PASSWORD` rotated for staging/prod
- [ ] No `secrets.yaml` with real values in git (`salesos/.gitignore` blocks `secrets.*`)
- [ ] Prometheus scrape JWT not committed — use `prometheus-token.example` → local `prometheus-token`
- [ ] Dependency scanners run on release branch (workflow: `salesos/.github/workflows/security-scan.yml`)
- [ ] Critical/High findings closed or CTO-signed exception recorded in PRC

## Scanner stubs (no cloud vendor required)

| Tool | Config | How to run |
|------|--------|------------|
| Gitleaks | `.gitleaks.toml` (root) / `salesos/.gitleaks.toml` | `gitleaks detect --source . --config .gitleaks.toml` |
| Trivy | `.trivyignore` | CI job in `security-scan.yml` |
| pip-audit / npm audit / Bandit / Semgrep | existing workflow jobs | `workflow_dispatch` on release branch |

## Compose / env patterns

| Wrong | Right |
|-------|--------|
| Hardcoded password in compose committed as prod | `${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD}` or documented **dev-only** default |
| JWT in git (`prometheus-token`) | Example file + gitignored real token |
| `JWT_SECRET=salesos-prod-secret` default | `${JWT_SECRET:?Set JWT_SECRET}` |

Root `docker-compose.yml` keeps **dev-only defaults** so local `docker compose up` works without a filled `.env`. Staging/prod compose files require explicit env (fail-fast `:?`).

## Generate local secrets

```bash
python -c "import secrets; print(secrets.token_hex(32))"
cp .env.example .env   # or salesos/.env.example → salesos/.env
# edit .env — never commit
```
