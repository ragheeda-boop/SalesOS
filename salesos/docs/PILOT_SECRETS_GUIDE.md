# SalesOS Pilot — Secrets Management Guide

> دليل إدارة الأسرار لبرنامج التجربة الأولية
> How to generate, populate, and secure secrets for staging

---

## Overview / نظرة عامة

**الأمان أولاً:** جميع الأسرار يجب أن تكون في ملفات `.env` المُستبعدة من Git، وليس في الكود أبداً.

### Files Involved / الملفات المعنية

| الملف | الوصف | مُستبعد من Git؟ |
|-------|-------|-----------------|
| `.env.staging` | متغيرات البيئة للاختبار | يجب أن يكون |
| `.env.production.template` | قالب للإنتاج | لا (قالب عام) |
| `.env` | البيئة المحلية | نعم |

---

## Step 1: Generate Secrets / توليد الأسرار

### PostgreSQL Password / كلمة مرور PostgreSQL

```powershell
# Generate a 32-byte hex string
openssl rand -hex 32

# Example output: a3f5b8c2e1d4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

### Neo4j Password / كلمة مرور Neo4j

```powershell
# Generate a 32-byte hex string
openssl rand -hex 32

# Example output: b4c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5
```

### JWT Secret / سر JWT

```powershell
# Generate a 64-byte hex string (more secure for JWT)
openssl rand -hex 64

# Example output: c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
```

### Grafana Admin Password / كلمة مرور Grafana

```powershell
# Generate a 16-byte hex string (sufficient for admin)
openssl rand -hex 16

# Example output: d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2
```

### OpenAI API Key (Optional) / مفتاح OpenAI (اختياري)

If using AI features during the pilot:

```
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy the key (starts with sk-)
```

---

## Step 2: Populate .env.staging / تعبئة ملف البيئة

### Copy the Template

```powershell
# If starting fresh
Copy-Item .env.staging .env.staging.backup

# Edit .env.staging with your generated secrets
notepad .env.staging
```

### Required Changes / التغييرات الإلزامية

Replace all `CHANGE_ME` values in `.env.staging`:

```bash
# ─── DATABASE ────────────────────────────────────────
POSTGRES_PASSWORD=<paste-openssl-rand-hex-32-output>

# ─── NEO4J ──────────────────────────────────────────
NEO4J_PASSWORD=<paste-openssl-rand-hex-32-output>

# ─── JWT ────────────────────────────────────────────
JWT_SECRET=<paste-openssl-rand-hex-64-output>

# ─── GRAFANA ────────────────────────────────────────
GRAFANA_PASSWORD=<paste-openssl-rand-hex-16-output>

# ─── OPENAI (optional) ──────────────────────────────
OPENAI_API_KEY=sk-<your-openai-key>

# ─── ERROR TRACKING (optional) ──────────────────────
SENTRY_DSN=https://<key>@sentry.io/<project-id>
```

### Example .env.staging (Populated)

```bash
# SalesOS Staging Environment
# NEVER commit this file to version control

NODE_ENV=staging

# Database
POSTGRES_USER=salesos
POSTGRES_PASSWORD=a3f5b8c2e1d4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
POSTGRES_DB=salesos

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=b4c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5
NEO4J_MAX_CONNECTIONS=50
NEO4J_CONNECTION_TIMEOUT=30
NEO4J_MAX_RETRIES=3

# Redis
REDIS_URL=redis://redis:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# API
NEXT_PUBLIC_API_URL=http://localhost:3000
API_URL=http://backend:8000

# JWT
JWT_SECRET=c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Sentry
SENTRY_DSN=

# Grafana
GRAFANA_PASSWORD=d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2

# Domain
DOMAIN=localhost

# Backup
BACKUP_RETENTION_DAYS=7
S3_BUCKET=
NOTIFY_WEBHOOK=
```

---

## Step 3: Secure .env Files / حماية ملفات البيئة

### Git Exclusion / استبعاد Git

The `.gitignore` already excludes common env files:

```gitignore
.env
.env.local
.env.*.local
```

**IMPORTANT:** `.env.staging` is NOT in `.gitignore` by default. Add it:

```powershell
# Add .env.staging to .gitignore
Add-Content -Path .gitignore -Value "`n# Staging secrets`n.env.staging`n.env.staging.*"
```

Or manually add these lines to `.gitignore`:

```gitignore
# Staging secrets (NEVER commit)
.env.staging
.env.staging.local
```

### File Permissions / صلاحيات الملف

On Linux/Mac staging server:

```bash
# Set restrictive permissions
chmod 600 .env.staging
chown salesos:salesos .env.staging

# Verify
ls -la .env.staging
# -rw------- 1 salesos salesos 1234 Jul 12 10:00 .env.staging
```

On Windows:

```powershell
# Restrict access to current user only
$acl = Get-Acl ".env.staging"
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    [System.Security.Principal.WindowsIdentity]::GetCurrent().Name,
    "FullControl",
    "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl ".env.staging" $acl
```

### Environment Variable Precedence / ترتيب الأولوية

Docker Compose reads `.env` in this order (later overrides earlier):

1. Shell environment variables (`$env:POSTGRES_PASSWORD`)
2. `.env` file in project root
3. `.env.staging` (must be specified explicitly)
4. Docker Compose `environment:` section

**Best Practice:** Use `.env.staging` explicitly:

```powershell
# Start with staging env
docker compose --env-file .env.staging -f infra/staging/docker-compose.staging.yml up -d
```

---

## Step 4: Verify No Secrets in Git / التحقق من عدم وجود أسرار في Git

### Check Currently Tracked Secrets

```powershell
# Search for any secrets in git history
git log --all --full-history -- "*.env" "*.env.*" | Select-String -Pattern "PASSWORD|SECRET|KEY|TOKEN"

# Check if .env.staging is tracked
git ls-files .env.staging
# Should return empty (not tracked)

# Check if any CHANGE_ME values are in the repo
git grep -r "CHANGE_ME" -- "*.py" "*.ts" "*.tsx" "*.js" "*.yml" "*.yaml" "*.json"
```

### Scan for Hardcoded Secrets

```powershell
# Search for common secret patterns
$patterns = @(
    "password\s*=\s*['\"][^'\"]+['\"]",
    "secret\s*=\s*['\"][^'\"]+['\"]",
    "api_key\s*=\s*['\"][^'\"]+['\"]",
    "token\s*=\s*['\"][^'\"]+['\"]",
    "sk-[a-zA-Z0-9]{20,}",          # OpenAI keys
    "eyJ[a-zA-Z0-9_-]+\.eyJ"         # JWT tokens
)

foreach ($pattern in $patterns) {
    $matches = git grep -r $pattern -- "*.py" "*.ts" "*.tsx" "*.js" "*.env*"
    if ($matches) {
        Write-Host "[WARNING] Potential secret found:" -ForegroundColor Yellow
        Write-Host $matches
    }
}
```

### Pre-Commit Hook (Recommended)

Install a secret-scanning pre-commit hook:

```powershell
# Install gitleaks (one-time)
choco install gitleaks  # Windows
# or: brew install gitleaks  # Mac

# Test against current repo
gitleaks detect --source . --verbose
```

### Verify .env.staging is Excluded

```powershell
# Final check — should return nothing
git status .env.staging
# Should show: .env.staging — untracked (good!)

# Ensure it's in .gitignore
Select-String -Path .gitignore -Pattern "env.staging"
# Should return a match
```

---

## Quick Reference / مرجع سريع

```bash
# ── Generate all secrets at once ──────────────────────
POSTGRES_PW=$(openssl rand -hex 32)
NEO4J_PW=$(openssl rand -hex 32)
JWT_SEC=$(openssl rand -hex 64)
GRAFANA_PW=$(openssl rand -hex 16)

echo "POSTGRES_PASSWORD=$POSTGRES_PW"
echo "NEO4J_PASSWORD=$NEO4J_PW"
echo "JWT_SECRET=$JWT_SEC"
echo "GRAFANA_PASSWORD=$GRAFANA_PW"

# ── Verify no secrets committed ───────────────────────
git ls-files | grep -i "\.env"
# Should only show .env.example and .env.production.template

git grep -r "CHANGE_ME" -- "*.py" "*.ts" "*.yml"
# Should return empty

# ── Copy secrets to staging server ────────────────────
scp .env.staging user@staging-server:/opt/salesos/.env.staging
ssh user@staging-server "chmod 600 /opt/salesos/.env.staging"
```

---

## Emergency Rotation / تدوير الأسرار الطارئ

If a secret is compromised:

```powershell
# 1. Generate new secrets
$NEW_POSTGRES = openssl rand -hex 32
$NEW_NEO4J = openssl rand -hex 32
$NEW_JWT = openssl rand -hex 64

# 2. Update .env.staging
# (edit the file with new values)

# 3. Restart all services
docker compose -f infra/staging/docker-compose.staging.yml down
docker compose -f infra/staging/docker-compose.staging.yml up -d

# 4. Verify services are healthy
.\scripts\pilot-verify.ps1 -BaseUrl "http://localhost:8000" -TenantId "pilot_tenant"

# 5. Invalidate all existing JWT tokens (if JWT secret changed)
# Users will need to re-login
```

---

*Last updated: 2026-07-12*
*Version: 1.0 — Pilot Launch*
*Linked: PILOT_LAUNCH_CHECKLIST.md, .env.staging*
