#Requires -Version 5.1
<#
.SYNOPSIS
    SalesOS External-Grade Security Audit Script
.DESCRIPTION
    Runs comprehensive security checks across the SalesOS codebase and outputs
    a JSON report with findings and severity levels.
.NOTES
    Run from the salesos/ repository root.
    Exit code 0 = no critical findings, 1 = critical findings present.
#>

param(
    [string]$OutputPath = "security-audit-report.json",
    [string]$BackendPath = "backend",
    [string]$FrontendPath = "frontend"
)

$ErrorActionPreference = "Continue"
$findings = @()
$startTime = Get-Date

function Add-Finding {
    param(
        [string]$Category,
        [string]$Check,
        [string]$Severity,
        [string]$Status,
        [string]$Details,
        [string]$File = "",
        [int]$Line = 0,
        [string]$Remediation = ""
    )
    $obj = New-Object PSObject -Property @{
        Category    = $Category
        Check       = $Check
        Severity    = $Severity
        Status      = $Status
        Details     = $Details
        File        = $File
        Line        = $Line
        Remediation = $Remediation
    }
    $script:findings += $obj
}

Write-Host "============================================"
Write-Host " SalesOS Security Audit"
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================"
Write-Host ""

# 1. HARDCODED SECRETS DETECTION
Write-Host "[1/9] Scanning for hardcoded secrets..."

$secretChecks = @(
    @{Pat = 'password\s*[:=]\s*["' + "'" + '][^"' + "'" + ']{6,}'; D = "Hardcoded password"}
    @{Pat = 'api[_-]?key\s*[:=]\s*["' + "'" + '][A-Za-z0-9_-]{20,}'; D = "Hardcoded API key"}
    @{Pat = 'secret[_-]?key\s*[:=]\s*["' + "'" + '][A-Za-z0-9_-]{16,}'; D = "Hardcoded secret key"}
    @{Pat = 'access[_-]?token\s*[:=]\s*["' + "'" + '][A-Za-z0-9_-]{20,}'; D = "Hardcoded access token"}
    @{Pat = 'ghp_[A-Za-z0-9]{36}'; D = "GitHub PAT detected"}
    @{Pat = 'AKIA[0-9A-Z]{16}'; D = "AWS Access Key detected"}
)

$pyFiles = Get-ChildItem -Path $BackendPath -Recurse -Include "*.py","*.js","*.ts","*.yaml","*.yml","*.json","*.toml","*.cfg" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '(test_|tests[/\\]|__pycache__|node_modules|\.next|venv|migrations|\.git)' }

foreach ($sc in $secretChecks) {
    $results = $pyFiles | Select-String -Pattern $sc.Pat -ErrorAction SilentlyContinue
    foreach ($m in $results) {
        if ($m.Path -match '(test_|_test\.|conftest|fixture|mock)') { continue }
        if ($m.Line -match '^\s*#') { continue }
        $trimmed = $m.Line.Trim()
        if ($trimmed.Length -gt 200) { $trimmed = $trimmed.Substring(0,200) + "..." }
        Add-Finding -Category "Secrets" -Check "Hardcoded Secrets" -Severity "Critical" -Status "Fail" `
            -Details "$($sc.D): $trimmed" -File $m.Path -Line $m.LineNumber `
            -Remediation "Move secret to environment variable or secrets manager"
    }
}

$secretsFailed = ($findings | Where-Object { $_.Check -eq "Hardcoded Secrets" -and $_.Status -eq "Fail" }).Count
if ($secretsFailed -eq 0) {
    Add-Finding -Category "Secrets" -Check "Hardcoded Secrets" -Severity "Critical" -Status "Pass" `
        -Details "No hardcoded secrets found in codebase"
}

# 2. ENV FILE GITIGNORE CHECK
Write-Host "[2/9] Checking .env files in .gitignore..."

$gitignoreMissing = @()
if (Test-Path ".gitignore") {
    $gi = Get-Content ".gitignore" -Raw
    foreach ($ef in @(".env", ".env.local", ".env.production", ".env.staging")) {
        if ($gi -notmatch [regex]::Escape($ef)) {
            $gitignoreMissing += $ef
        }
    }
} else {
    $gitignoreMissing = @(".env", ".env.local", ".env.production", ".env.staging")
}

if ($gitignoreMissing.Count -gt 0) {
    Add-Finding -Category "Secrets" -Check ".env Gitignore" -Severity "Critical" -Status "Fail" `
        -Details "Missing from .gitignore: $($gitignoreMissing -join ', ')" `
        -Remediation "Add all .env* patterns to .gitignore"
} else {
    Add-Finding -Category "Secrets" -Check ".env Gitignore" -Severity "Critical" -Status "Pass" `
        -Details "All .env files are properly gitignored"
}

# 3. DEBUG MODE IN PRODUCTION
Write-Host "[3/9] Checking debug mode in production configs..."

if (Test-Path "docker-compose.prod.yml") {
    $prod = Get-Content "docker-compose.prod.yml" -Raw
    if ($prod -match 'SALESOS_DEBUG\s*[:=]\s*true') {
        Add-Finding -Category "Configuration" -Check "Debug Mode in Production" -Severity "High" -Status "Fail" `
            -Details "SALESOS_DEBUG=true found in production compose" `
            -Remediation "Set SALESOS_DEBUG=false in production"
    } else {
        Add-Finding -Category "Configuration" -Check "Debug Mode in Production" -Severity "High" -Status "Pass" `
            -Details "Debug mode is disabled in production compose"
    }
} else {
    Add-Finding -Category "Configuration" -Check "Debug Mode in Production" -Severity "Medium" -Status "Warn" `
        -Details "docker-compose.prod.yml not found"
}

$configPy = Join-Path $BackendPath "app/config.py"
if (Test-Path $configPy) {
    $cfg = Get-Content $configPy -Raw
    if ($cfg -match 'debug:\s*bool\s*=\s*True') {
        Add-Finding -Category "Configuration" -Check "Debug Default" -Severity "Medium" -Status "Warn" `
            -Details "debug=True is the default in config.py" `
            -Remediation "Consider defaulting to False and requiring explicit opt-in"
    }
}

# 4. CORS ORIGINS CHECK
Write-Host "[4/9] Checking CORS configuration..."

if (Test-Path $configPy) {
    $cfg = Get-Content $configPy -Raw
    if ($cfg -match 'allowed_hosts.*=.*"\*"') {
        Add-Finding -Category "Configuration" -Check "CORS Wildcard" -Severity "High" -Status "Fail" `
            -Details "CORS allows all origins (wildcard)" `
            -Remediation "Restrict CORS to specific allowed origins"
    } else {
        Add-Finding -Category "Configuration" -Check "CORS Restrictive" -Severity "High" -Status "Pass" `
            -Details "CORS origins are configurable and not wildcarded by default"
    }
}

# 5. RATE LIMITING CHECK
Write-Host "[5/9] Verifying rate limiting on auth endpoints..."

$mwPath = Join-Path $BackendPath "app/common/middleware.py"
if (Test-Path $mwPath) {
    $mw = Get-Content $mwPath -Raw
    if ($mw -match 'class RateLimitMiddleware') {
        if ($mw -match '/api/v1/identity') {
            Add-Finding -Category "Authentication" -Check "Rate Limiting Identity" -Severity "High" -Status "Pass" `
                -Details "Identity endpoints have dedicated rate limit tier"
        } else {
            Add-Finding -Category "Authentication" -Check "Rate Limiting Identity" -Severity "High" -Status "Fail" `
                -Details "No dedicated rate limit for auth endpoints"
        }
        if ($mw -match 'Retry-After') {
            Add-Finding -Category "Authentication" -Check "Retry-After Header" -Severity "Medium" -Status "Pass" `
                -Details "429 responses include Retry-After header"
        } else {
            Add-Finding -Category "Authentication" -Check "Retry-After Header" -Severity "Medium" -Status "Fail" `
                -Details "Missing Retry-After header on 429 responses"
        }
    } else {
        Add-Finding -Category "Authentication" -Check "Rate Limiting" -Severity "High" -Status "Fail" `
            -Details "No RateLimitMiddleware found"
    }
}

# 6. SQL INJECTION DETECTION
Write-Host "[6/9] Checking for SQL injection risks..."

$sqlPats = @(
    'text\s*\(\s*f["' + "'" + ']'
    'execute\s*\(\s*f["' + "'" + ']'
    '\.raw\s*\(\s*f["' + "'" + ']'
)

foreach ($sp in $sqlPats) {
    $hits = $pyFiles | Select-String -Pattern $sp -ErrorAction SilentlyContinue
    foreach ($h in $hits) {
        if ($h.Path -match 'test') { continue }
        if ($h.Line -match ':param|:name') { continue }
        $tline = $h.Line.Trim()
        if ($tline.Length -gt 200) { $tline = $tline.Substring(0,200) + "..." }
        Add-Finding -Category "Injection" -Check "SQL Injection Risk" -Severity "Critical" -Status "Fail" `
            -Details "Potential SQL injection: $tline" -File $h.Path -Line $h.LineNumber `
            -Remediation "Use parameterized queries with named bind params"
    }
}

$sqlFailed = ($findings | Where-Object { $_.Check -eq "SQL Injection Risk" -and $_.Status -eq "Fail" }).Count
if ($sqlFailed -eq 0) {
    Add-Finding -Category "Injection" -Check "SQL Injection Risk" -Severity "Critical" -Status "Pass" `
        -Details "No SQL injection risks found"
}

# 7. JWT SECRET LENGTH CHECK
Write-Host "[7/9] Verifying JWT secret length..."

$jwtMinBits = 256
$jwtFound = $false
$envFiles = Get-ChildItem -Path "." -Filter ".env*" -File -ErrorAction SilentlyContinue

foreach ($ef in $envFiles) {
    $lines = Get-Content $ef.FullName -ErrorAction SilentlyContinue
    foreach ($ln in $lines) {
        if ($ln -match '^JWT_SECRET_KEY\s*=\s*(.+)') {
            $jwtFound = $true
            $sv = $Matches[1].Trim('"').Trim("'")
            $bits = $sv.Length * 8
            if ($bits -lt $jwtMinBits) {
                Add-Finding -Category "Cryptography" -Check "JWT Secret Length" -Severity "Critical" -Status "Fail" `
                    -Details "JWT secret is only $bits bits minimum is $jwtMinBits bits" `
                    -Remediation "Generate a 256-bit random secret"
            } else {
                Add-Finding -Category "Cryptography" -Check "JWT Secret Length" -Severity "Critical" -Status "Pass" `
                    -Details "JWT secret is $bits bits which is >= $jwtMinBits required"
            }
        }
    }
}

if (-not $jwtFound) {
    Add-Finding -Category "Cryptography" -Check "JWT Secret Length" -Severity "Info" -Status "Warn" `
        -Details "JWT_SECRET_KEY not found in .env files" `
        -Remediation "Verify JWT_SECRET_KEY is set to >= 256-bit value in production"
}

# 8. STACK TRACE EXPOSURE CHECK
Write-Host "[8/9] Checking for exposed stack traces..."

$mainPy = Join-Path $BackendPath "app/main.py"
if (Test-Path $mainPy) {
    $main = Get-Content $mainPy -Raw
    if ($main -match 'str\(exc\)') {
        Add-Finding -Category "Information Disclosure" -Check "Stack Trace in Errors" -Severity "High" -Status "Fail" `
            -Details "Exception details exposed in 500 error responses via str(exc)" `
            -Remediation "Return generic error message in production; log details server-side only"
    } else {
        Add-Finding -Category "Information Disclosure" -Check "Stack Trace in Errors" -Severity "High" -Status "Pass" `
            -Details "500 error handler does not expose exception details"
    }
}

# 9. SECURITY HEADERS CHECK
Write-Host "[9/9] Verifying security headers..."

if (Test-Path $mwPath) {
    $mw = Get-Content $mwPath -Raw
    $headers = @(
        @{P = "strict-transport-security"; N = "HSTS"}
        @{P = "x-content-type-options"; N = "X-Content-Type-Options"}
        @{P = "x-frame-options"; N = "X-Frame-Options"}
        @{P = "referrer-policy"; N = "Referrer-Policy"}
        @{P = "permissions-policy"; N = "Permissions-Policy"}
        @{P = "content-security-policy"; N = "Content-Security-Policy"}
    )
    foreach ($h in $headers) {
        if ($mw -match $h.P) {
            Add-Finding -Category "Headers" -Check "Header: $($h.N)" -Severity "Medium" -Status "Pass" `
                -Details "$($h.N) header is set in SecurityHeadersMiddleware"
        } else {
            Add-Finding -Category "Headers" -Check "Header: $($h.N)" -Severity "Medium" -Status "Fail" `
                -Details "$($h.N) header is missing" `
                -Remediation "Add $($h.N) header to SecurityHeadersMiddleware"
        }
    }
}

# BONUS CHECKS
Write-Host "  [bonus] Checking CSRF, passwords, cookies..."

# CSRF
if (Test-Path $mwPath) {
    $mw = Get-Content $mwPath -Raw
    if ($mw -match 'CsrfEnforcementMiddleware') {
        Add-Finding -Category "Authentication" -Check "CSRF Protection" -Severity "High" -Status "Pass" `
            -Details "CSRF enforcement middleware is active"
    } else {
        Add-Finding -Category "Authentication" -Check "CSRF Protection" -Severity "High" -Status "Fail" `
            -Details "No CSRF enforcement middleware found"
    }
}

# Password Policy
$schPath = Join-Path $BackendPath "app/modules/identity/schemas.py"
if (Test-Path $schPath) {
    $sch = Get-Content $schPath -Raw
    if ($sch -match 'min_length=12') {
        Add-Finding -Category "Authentication" -Check "Password Min Length" -Severity "Medium" -Status "Pass" `
            -Details "Minimum password length is 12 characters"
    }
    if ($sch -match 'validate_password_strength') {
        Add-Finding -Category "Authentication" -Check "Password Complexity" -Severity "Medium" -Status "Pass" `
            -Details "Password complexity validation is enforced"
    }
}

# Account Lockout
$svcPath = Join-Path $BackendPath "app/modules/identity/service.py"
if (Test-Path $svcPath) {
    $svc = Get-Content $svcPath -Raw
    if ($svc -match 'MAX_FAILED_ATTEMPTS') {
        Add-Finding -Category "Authentication" -Check "Account Lockout" -Severity "Medium" -Status "Pass" `
            -Details "Account lockout after failed attempts is implemented"
    }
}

# Cookie Security
$rtPath = Join-Path $BackendPath "app/modules/identity/router.py"
if (Test-Path $rtPath) {
    $rt = Get-Content $rtPath -Raw
    if ($rt -match 'httponly=True') {
        Add-Finding -Category "Authentication" -Check "Cookie HttpOnly" -Severity "Medium" -Status "Pass" `
            -Details "Refresh token cookie has HttpOnly flag"
    }
    if ($rt -match 'secure=True') {
        Add-Finding -Category "Authentication" -Check "Cookie Secure" -Severity "Medium" -Status "Pass" `
            -Details "Refresh token cookie has Secure flag"
    }
    if ($rt -match 'samesite.*strict') {
        Add-Finding -Category "Authentication" -Check "Cookie SameSite" -Severity "Medium" -Status "Pass" `
            -Details "Refresh token cookie has SameSite=Strict"
    }
}

# GENERATE REPORT
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$critCount = ($findings | Where-Object { $_.Severity -eq "Critical" -and $_.Status -eq "Fail" }).Count
$highCount = ($findings | Where-Object { $_.Severity -eq "High" -and $_.Status -eq "Fail" }).Count
$medCount = ($findings | Where-Object { $_.Severity -eq "Medium" -and $_.Status -eq "Fail" }).Count
$lowCount = ($findings | Where-Object { $_.Severity -eq "Low" -and $_.Status -eq "Fail" }).Count
$passCount = ($findings | Where-Object { $_.Status -eq "Pass" }).Count
$warnCount = ($findings | Where-Object { $_.Status -eq "Warn" }).Count
$totalFailed = $critCount + $highCount + $medCount + $lowCount
$score = if ($findings.Count -gt 0) { [math]::Round(($passCount / $findings.Count) * 100, 1) } else { 0 }

$report = @{
    metadata = @{
        tool       = "salesos-security-audit"
        version    = "1.0.0"
        timestamp  = (Get-Date -Format "o")
        duration_s = [math]::Round($duration, 2)
    }
    summary = @{
        total_checks = $findings.Count
        passed       = $passCount
        warnings     = $warnCount
        failed       = $totalFailed
        critical     = $critCount
        high         = $highCount
        medium       = $medCount
        low          = $lowCount
        score        = $score
    }
    findings = $findings
}

$report | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputPath -Encoding UTF8

Write-Host ""
Write-Host "============================================"
Write-Host " AUDIT RESULTS"
Write-Host "============================================"
Write-Host " Total checks:  $($findings.Count)"
Write-Host " Passed:        $passCount"
Write-Host " Warnings:      $warnCount"
Write-Host " Failed:        $totalFailed"
Write-Host "   Critical:    $critCount"
Write-Host "   High:        $highCount"
Write-Host "   Medium:      $medCount"
Write-Host "   Low:         $lowCount"
Write-Host " Score:         $score%"
Write-Host " Duration:      $([math]::Round($duration, 2))s"
Write-Host " Report:        $OutputPath"
Write-Host "============================================"

if ($critCount -gt 0) {
    Write-Host ""
    Write-Host "CRITICAL FINDINGS:"
    foreach ($f in ($findings | Where-Object { $_.Severity -eq "Critical" -and $_.Status -eq "Fail" })) {
        $msg = "  [{0}] {1}: {2}" -f $f.Category, $f.Check, $f.Details
        Write-Host $msg
        if ($f.Remediation -ne "") {
            Write-Host "    Fix: $($f.Remediation)"
        }
    }
}

exit [int]($critCount -gt 0)
