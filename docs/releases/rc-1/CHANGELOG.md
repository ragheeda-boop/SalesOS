# Changelog — v5.1.0-rc1

## [RC-1] 2026-08-06

### Quality
- Removed `eslint.ignoreDuringBuilds` bypass — lint now blocks production builds
- Promoted 6 ESLint rules from warn to error (no-explicit-any, no-empty-interface, exhaustive-deps, no-tailwind-color-classes, no-hardcoded-colors)
- Created Prettier config (100 width, 2-space, semicolons) + format scripts
- Created .editorconfig for consistent encoding/whitespace
- Upgraded Ruff ^0.4 → ^0.11, added PL/RUF/PERF rule sets
- Tightened Mypy: ignore_missing_imports=false, 6 new strictness flags, domains/ added
- Coverage threshold raised 55% → 65% with branch coverage

### Dependencies
- Poetry: Docker version aligned to 2.4.1 (matches lock file), poetry-core pinned >=2.0
- Docker images pinned: pgbouncer 1.23.1, prometheus v3.3.0, grafana 11.6.0, exporters
- Kafka standardized: all 4 compose files → 7.7.2

### Security
- JWT templates aligned to RS256, validator rejects non-RS256 values
- Added TrustedHostMiddleware to backend middleware stack
- Added CSP + Cross-Origin-Opener-Policy to Next.js frontend
- Synced .env.example with 13+ missing variables

### CI/CD
- Fixed broken deploy.yml notify job reference
- Created release-gates.yml workflow
- Added concurrency group to docker-smoke.yml

### Observability
- Deprecated duplicate MetricsTracker (legacy collector)
- Commented out 4 alert rules requiring undeployed exporters
- Added 3 production uptime alerts (BackendDown, PostgresDown, RedisDown)

### Verification
- All 14 services healthy
- TypeScript: 0 errors
- Frontend: HTTP 200
- Backend: database/cache/graph/redis connected
