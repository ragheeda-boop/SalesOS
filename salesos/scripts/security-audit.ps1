<#
.SYNOPSIS
  SalesOS Security Audit — automated security gate.
.DESCRIPTION
  Runs five security checks:
    1. npm audit in the frontend directory
    2. .env files tracked in git
    3. Hardcoded secrets patterns in source code
    4. WebSocket tokens in URL query strings
    5. K8s secrets files with placeholder values
.OUTPUTS
  Pass/fail status for each check with details.
#>

param(
  [string]$RepoRoot = (Resolve-Path "$PSScriptRoot/..")
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date
$allPassed = $true
$results = @()

# ── Check 1: npm audit ─────────────────────────────────────────
Write-Host "`n[1/5] Running npm audit in frontend..." -ForegroundColor Cyan
$frontendDir = Join-Path $RepoRoot "frontend"
$npmAuditPassed = $true
$npmAuditDetail = ""

if (Test-Path "$frontendDir/package.json") {
  try {
    $auditOutput = & npm audit --json 2>&1 | Out-String
    $auditJson = $auditOutput | ConvertFrom-Json

    if ($auditJson.metadata -and $auditJson.metadata.vulnerabilities) {
      $vulns = $auditJson.metadata.vulnerabilities
      $critical = if ($vulns.critical) { $vulns.critical } else { 0 }
      $high = if ($vulns.high) { $vulns.high } else { 0 }
      $moderate = if ($vulns.moderate) { $vulns.moderate } else { 0 }

      if ($critical -gt 0 -or $high -gt 0) {
        $npmAuditPassed = $false
        $npmAuditDetail = "Found $critical critical, $high high, $moderate moderate vulnerabilities"
      } else {
        $npmAuditDetail = "No critical/high vulnerabilities ($moderate moderate)"
      }
    } else {
      $npmAuditDetail = "npm audit completed — no vulnerabilities found"
    }
  } catch {
    $npmAuditPassed = $false
    $npmAuditDetail = "npm audit failed to run: $($_.Exception.Message)"
  }
} else {
  $npmAuditDetail = "frontend/package.json not found — skipped"
}

$results += @{ check = "npm_audit"; passed = $npmAuditPassed; detail = $npmAuditDetail }
if (-not $npmAuditPassed) { $allPassed = $false }

# ── Check 2: .env files in git ─────────────────────────────────
Write-Host "[2/5] Checking for .env files tracked in git..." -ForegroundColor Cyan
$envGitPassed = $true
$envGitDetail = ""

try {
  $trackedEnvFiles = & git -C $RepoRoot ls-files -- '*.env' '.env*' '*.env.*' 2>&1 | Out-String
  $envFiles = $trackedEnvFiles.Trim() -split "`n" | Where-Object { $_.Trim() -ne "" }

  if ($envFiles.Count -gt 0) {
    $envGitPassed = $false
    $envGitDetail = "Tracked .env files found: $($envFiles -join ', ')"
  } else {
    $envGitDetail = "No .env files tracked in git"
  }
} catch {
  $envGitDetail = "git ls-files failed: $($_.Exception.Message)"
}

$results += @{ check = "env_in_git"; passed = $envGitPassed; detail = $envGitDetail }
if (-not $envGitPassed) { $allPassed = $false }

# ── Check 3: Hardcoded secrets patterns ────────────────────────
Write-Host "[3/5] Scanning for hardcoded secrets..." -ForegroundColor Cyan
$secretsPassed = $true
$secretsDetail = ""
$findings = @()

$secretPatterns = @(
  @{ pattern = '(?i)api[_-]?key\s*=\s*[''"][A-Za-z0-9]{20,}'; desc = "Hardcoded API key" },
  @{ pattern = '(?i)secret\s*=\s*[''"][A-Za-z0-9]{16,}'; desc = "Hardcoded secret" },
  @{ pattern = '(?i)password\s*=\s*[''"][^''"]{8,}'; desc = "Hardcoded password" },
  @{ pattern = '(?i)token\s*=\s*[''"][A-Za-z0-9\-._]{20,}'; desc = "Hardcoded token" },
  @{ pattern = '(?i)aws[_-]?access[_-]?key[_-]?id\s*=\s*[''"]?(?:A3T[A-Z0-9]|AKIA)[A-Z0-9]{16}'; desc = "AWS access key" },
  @{ pattern = '(?i)BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY'; desc = "Private key in source" }
)

$sourceExtensions = @("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml", "*.toml", "*.json")
$excludeDirs = @("node_modules", ".next", "venv", ".venv", "__pycache__", "dist", "build", ".git", "reports")

foreach ($ext in $sourceExtensions) {
  $files = Get-ChildItem -Recurse -File -Path $RepoRoot -Include $ext -ErrorAction SilentlyContinue |
    Where-Object {
      $fullPath = $_.FullName
      -not ($excludeDirs | Where-Object { $fullPath -like "*\$_\*" })
    }

  foreach ($file in $files) {
    # Skip .env files themselves
    if ($file.Name -match '^\.env') { continue }
    # Skip example/template files
    if ($file.Name -match '\.example$|\.template$|\.sample$') { continue }

    try { $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue } catch { $content = $null }
    if (-not $content) { continue }

    foreach ($sp in $secretPatterns) {
      if ($content -match $sp.pattern) {
        $relPath = $file.FullName.Replace("$RepoRoot\", "").Replace("$RepoRoot/", "")
        $findings += "$($sp.desc) in $relPath"
      }
    }
  }
}

if ($findings.Count -gt 0) {
  $secretsPassed = $false
  $secretsDetail = "Found $($findings.Count) potential hardcoded secret(s):`n  $($findings -join '`n  ')"
} else {
  $secretsDetail = "No hardcoded secrets detected"
}

$results += @{ check = "hardcoded_secrets"; passed = $secretsPassed; detail = $secretsDetail }
if (-not $secretsPassed) { $allPassed = $false }

# ── Check 4: WebSocket tokens in URL query strings ─────────────
Write-Host "[4/5] Scanning for WebSocket tokens in URLs..." -ForegroundColor Cyan
$wsTokenPassed = $true
$wsTokenDetail = ""
$wsTokenFindings = @()

$wsTokenPatterns = @(
  @{ pattern = '(?i)new\s+WebSocket\s*\([^)]*\?token='; desc = "Token passed as URL query parameter in WebSocket" },
  @{ pattern = '(?i)ws[_-]?url\s*=\s*[`"''][^`"'']*\?token='; desc = "Token in WebSocket URL variable" },
  @{ pattern = '(?i)wss?://[^`"'']*\$\{.*token\}'; desc = "Interpolated token in WebSocket URL" }
)

foreach ($ext in @("*.ts", "*.tsx", "*.js", "*.jsx")) {
  $files = Get-ChildItem -Recurse -File -Path $RepoRoot -Include $ext -ErrorAction SilentlyContinue |
    Where-Object {
      $fullPath = $_.FullName
      -not ($excludeDirs | Where-Object { $fullPath -like "*\$_\*" })
    }

  foreach ($file in $files) {
    try { $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue } catch { $content = $null }
    if (-not $content) { continue }

    foreach ($wp in $wsTokenPatterns) {
      if ($content -match $wp.pattern) {
        $relPath = $file.FullName.Replace("$RepoRoot\", "").Replace("$RepoRoot/", "")
        $wsTokenFindings += "$($wp.desc) in $relPath"
      }
    }
  }
}

if ($wsTokenFindings.Count -gt 0) {
  $wsTokenPassed = $false
  $wsTokenDetail = "Found $($wsTokenFindings.Count) token-in-URL issue(s):`n  $($wsTokenFindings -join '`n  ')"
} else {
  $wsTokenDetail = "No WebSocket tokens found in URL query strings"
}

$results += @{ check = "ws_token_in_url"; passed = $wsTokenPassed; detail = $wsTokenDetail }
if (-not $wsTokenPassed) { $allPassed = $false }

# ── Check 5: K8s secrets with placeholder values ──────────────
Write-Host "[5/5] Checking K8s secrets for placeholder values..." -ForegroundColor Cyan
$k8sSecretsPassed = $true
$k8sSecretsDetail = ""
$k8sFindings = @()

$k8sSecretFiles = Get-ChildItem -Recurse -File -Path $RepoRoot -Include "secrets.yaml","secrets.yml","secrets*.yaml" -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notlike "*\.template*" -and $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*\.git*" }

foreach ($file in $k8sSecretFiles) {
  try { $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue } catch { $content = $null }
  if (-not $content) { continue }

  if ($content -match 'CHANGE_ME') {
    $relPath = $file.FullName.Replace("$RepoRoot\", "").Replace("$RepoRoot/", "")
    $k8sFindings += "$relPath contains CHANGE_ME placeholder values — not production-ready"
  }
}

if ($k8sFindings.Count -gt 0) {
  $k8sSecretsPassed = $false
  $k8sSecretsDetail = "Found $($k8sFindings.Count) issue(s):`n  $($k8sFindings -join '`n  ')"
} else {
  $k8sSecretsDetail = "No K8s secrets files with placeholder values detected"
}

$results += @{ check = "k8s_secrets_placeholders"; passed = $k8sSecretsPassed; detail = $k8sSecretsDetail }
if (-not $k8sSecretsPassed) { $allPassed = $false }

# ── Summary ────────────────────────────────────────────────────
$duration = (Get-Date) - $startTime
Write-Host "`n============================================"
Write-Host "  SALESOS SECURITY AUDIT REPORT"
Write-Host "============================================"

foreach ($r in $results) {
  if ($r.passed) {
    Write-Host "  PASS  $($r.check)" -ForegroundColor Green
  } else {
    Write-Host "  FAIL  $($r.check)" -ForegroundColor Red
  }
  Write-Host "        $($r.detail)" -ForegroundColor Gray
}

Write-Host ""
if ($allPassed) {
  Write-Host "RESULT: ALL CHECKS PASSED" -ForegroundColor Green
} else {
  Write-Host "RESULT: ONE OR MORE CHECKS FAILED" -ForegroundColor Red
}
Write-Host "Duration: $([math]::Round($duration.TotalSeconds, 1))s"
Write-Host ""

$report = @{
  timestamp    = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
  all_passed   = $allPassed
  checks       = $results
  duration_ms  = [math]::Round($duration.TotalMilliseconds, 0)
}

$reportPath = Join-Path $RepoRoot "reports/security-audit-report.json"
if (-not (Test-Path (Split-Path $reportPath))) {
  New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
}
$report | ConvertTo-Json -Depth 5 | Out-File -FilePath $reportPath -Encoding utf8
Write-Host "Report saved to reports/security-audit-report.json" -ForegroundColor Gray

if (-not $allPassed) { exit 1 }
