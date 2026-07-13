# Branch Protection Rules

> Enforced via GitHub branch protection settings. All rules are mandatory.

---

## Main Branch (`main`)

### Required Status Checks
| Check | Required | Description |
|-------|----------|-------------|
| `CI` pipeline | Yes | Full CI must pass (lint, types, tests, security, build) |
| `Security Scan` | Yes | Trivy, bandit, pip-audit, npm audit |
| `Arch Compliance` | Yes | Architecture compliance ≥ 95% |
| `Docker Smoke` | Yes | Container builds and starts successfully |

### Protection Rules
- **Require pull request reviews**: 2 approving reviews required
- **Dismiss stale reviews**: New commits dismiss previous approvals
- **Require review from code owners**: Enabled
- **Require status checks**: All above checks must pass before merge
- **Require branches to be up to date**: Branch must be rebased/merged with main
- **Require conversation resolution**: All PR conversations must be resolved
- **Require signed commits**: GPG signing recommended
- **Require linear history**: Merge commits allowed (no force push)
- **Require force push**: Denied
- **Require deployment**: No (manual trigger only)
- **Restrict force pushes**: Allowed to designated admins only
- **Allow deletions**: Denied

### Merge Strategy
- **Squash merge**: Preferred for feature branches
- **Merge commit**: Allowed for large features with multiple logical commits
- **Rebase**: Allowed for clean linear history

---

## Develop Branch (`develop`)

### Required Status Checks
| Check | Required | Description |
|-------|----------|-------------|
| `CI` pipeline | Yes | Lint, types, unit tests, security |
| `Docker Smoke` | Yes | Container builds and starts |

### Protection Rules
- **Require pull request reviews**: 1 approving review required
- **Dismiss stale reviews**: Enabled
- **Require status checks**: All above checks must pass
- **Require branches to be up to date**: Yes
- **Require force push**: Denied
- **Allow deletions**: Denied

### Purpose
- Integration branch for all features before release
- Staging environment deploys from `develop`
- Release branches are cut from `develop`

---

## Feature Branch Naming Convention

### Pattern: `type/scope-description`

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/*` | New features | `feat/search-hybrid-ranking` |
| `fix/*` | Bug fixes | `fix/auth-token-expiry` |
| `chore/*` | Maintenance tasks | `chore/upgrade-dependencies` |
| `docs/*` | Documentation only | `docs/api-endpoint-guide` |
| `refactor/*` | Code refactoring | `refactor/scoring-engine` |
| `test/*` | Test additions/fixes | `test/entity-resolution` |
| `perf/*` | Performance improvements | `perf/search-index-optimization` |
| `security/*` | Security fixes | `security/csrf-hardening` |
| `hotfix/*` | Emergency production fixes | `hotfix/auth-bypass` |

### Branch Naming Rules
- Use lowercase with hyphens (kebab-case)
- Keep scope concise (2-4 words max)
- Prefix with appropriate type
- Example: `feat/entity-resolution-merge-pipeline`

---

## Commit Message Convention (Conventional Commits)

### Format
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types
| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(search): add hybrid ranking` |
| `fix` | Bug fix | `fix(auth): resolve token refresh race condition` |
| `docs` | Documentation | `docs(api): update search endpoint docs` |
| `style` | Formatting (no logic change) | `style(frontend): fix button alignment` |
| `refactor` | Code restructuring | `refactor(scoring): extract decision engine` |
| `perf` | Performance improvement | `perf(search): add trigram index` |
| `test` | Test additions | `test(company): add entity resolution tests` |
| `chore` | Build/tooling changes | `chore(ci): upgrade action versions` |
| `security` | Security fix | `security(auth): patch CSRF vulnerability` |
| `revert` | Revert commit | `revert: revert feature X` |

### Scopes
| Scope | Domain |
|-------|--------|
| `auth` | Authentication / Identity |
| `search` | Search domain |
| `company` | Company domain |
| `scoring` | Scoring engine |
| `timeline` | Timeline domain |
| `workflow` | Workflow engine |
| `ai` | AI / LLM integration |
| `crm` | CRM domain |
| `frontend` | Frontend UI |
| `backend` | Backend API |
| `ci` | CI/CD pipeline |
| `docker` | Docker / deployment |
| `db` | Database / migrations |

### Examples
```
feat(search): implement hybrid full-text + semantic search with RRF fusion

- Add pg_trgm trigram matching for fuzzy text search
- Integrate pgvector cosine similarity for semantic search
- Implement Reciprocal Rank Fusion for result combination
- Coverage: 93% (exceeds 85% threshold)

Closes #123
```

```
fix(auth): resolve CSRF token validation bypass

Previously, CSRF tokens were not validated on OPTIONS requests,
allowing potential cross-site request forgery. Added validation
middleware that rejects all state-changing requests without valid
CSRF tokens.

Security: CRITICAL
Fixes: BUG-004
```

---

## Enforcement via GitHub API

### Setup Script
```bash
# Install gh CLI and authenticate first
gh api repos/{owner}/{repo}/branches/main/protection -X PUT -f required_status_checks='{"strict":true,"contexts":["CI","Security Scan","Arch Compliance","Docker Smoke"]}' -f enforce_admins=true -f required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' -f restrictions=null -f allow_force_pushes=false -f allow_deletions=false

gh api repos/{owner}/{repo}/branches/develop/protection -X PUT -f required_status_checks='{"strict":true,"contexts":["CI","Docker Smoke"]}' -f enforce_admins=false -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' -f restrictions=null -f allow_force_pushes=false -f allow_deletions=false
```

---

## Quick Reference

| Branch | Reviews | CI Required | Force Push | Delete | Stale Review Dismiss |
|--------|---------|-------------|------------|--------|---------------------|
| `main` | 2 | Yes (full) | Denied | Denied | Yes |
| `develop` | 1 | Yes (core) | Denied | Denied | Yes |
| `feat/*` | — | No | Allowed | Allowed | — |
| `fix/*` | — | No | Allowed | Allowed | — |
| `hotfix/*` | — | No | Allowed | Allowed | — |
