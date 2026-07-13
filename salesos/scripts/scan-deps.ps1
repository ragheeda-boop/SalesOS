#Requires -Version 5.1
<#
.SYNOPSIS
    SalesOS Dependency Vulnerability Scanner
.DESCRIPTION
    Scans Python (pip-audit) and frontend (npm audit) dependencies for
    known vulnerabilities. Reports critical/high findings and suggests upgrades.
.NOTES
    Run from the salesos/ repository root.
    Requires: pip-audit (pip install pip-audit), npm
#>

param(
    [string]$BackendPath = "backend",
    [string]$FrontendPath = "frontend",
    [string]$OutputPath = "dep-audit-report.json"
)

$ErrorActionPreference = "Continue"
$findings = @()
$startTime = Get-Date

function Add-DepFinding {
    param(
        [string]$Ecosystem,
        [string]$Package,
        [string]$InstalledVersion,
        [string]$FixedVersion,
        [string]$Severity,
        [string]$Advisory,
        [string]$Title
    )
    $script:findings += [PSCustomObject]@{
        Ecosystem        = $Ecosystem
        Package          = $Package
        InstalledVersion = $InstalledVersion
        FixedVersion     = $FixedVersion
        Severity         = $Severity
        Advisory         = $Advisory
        Title            = $Title
    }
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " SalesOS Dependency Vulnerability Scanner" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────────────────────────────────────
# 1. PYTHON DEPENDENCIES (pip-audit)
# ──────────────────────────────────────────────────────────────────────────
Write-Host "[1/2] Scanning Python dependencies..." -ForegroundColor Yellow

$pipAuditAvailable = $null -ne (Get-Command pip-audit -ErrorAction SilentlyContinue)

if ($pipAuditAvailable) {
    $requirementsPath = Join-Path $BackendPath "requirements.txt"
    $pipAuditArgs = @("--format", "json", "--output", "-")

    if (Test-Path $requirementsPath) {
        $pipAuditArgs += "--requirement"
        $pipAuditArgs += $requirementsPath
    }

    Write-Host "  Running pip-audit..." -ForegroundColor Gray
    try {
        $pipResult = & pip-audit @pipAuditArgs 2>&1 | Out-String
        $pipData = $pipResult | ConvertFrom-Json -ErrorAction SilentlyContinue

        if ($pipData -and $pipData.dependencies) {
            foreach ($dep in $pipData.dependencies) {
                if ($dep.vulns) {
                    foreach ($vuln in $dep.vulns) {
                        $severity = if ($vuln.fix_versions -and $vuln.fix_versions.Count -gt 0) {
                            "High"
                        } else {
                            "Critical"
                        }
                        Add-DepFinding -Ecosystem "Python" -Package $dep.name `
                            -InstalledVersion $dep.version `
                            -FixedVersion ($vuln.fix_versions -join ", ") `
                            -Severity $severity `
                            -Advisory $vuln.id `
                            -Title $vuln.description
                    }
                }
            }
            $pythonTotal = $pipData.dependencies.Count
            $pythonVulns = ($pipData.dependencies | Where-Object { $_.vulns -and $_.vulns.Count -gt 0 }).Count
            Write-Host "  Python: $pythonVulns/$pythonTotal packages with vulnerabilities" -ForegroundColor $(if ($pythonVulns -gt 0) { "Red" } else { "Green" })
        } else {
            Write-Host "  Python: pip-audit returned no dependency data" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Python: pip-audit failed — $_" -ForegroundColor Red
    }
} else {
    Write-Host "  pip-audit not found. Install with: pip install pip-audit" -ForegroundColor Yellow
    Write-Host "  Attempting fallback: pip check..." -ForegroundColor Gray
    try {
        $pipCheck = & pip check 2>&1 | Out-String
        if ($pipCheck -match "No broken requirements") {
            Write-Host "  pip check: No broken requirements found" -ForegroundColor Green
        } else {
            Write-Host "  pip check output: $pipCheck" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  pip check also failed" -ForegroundColor Red
    }
}

# ──────────────────────────────────────────────────────────────────────────
# 2. FRONTEND DEPENDENCIES (npm audit)
# ──────────────────────────────────────────────────────────────────────────
Write-Host "[2/2] Scanning frontend dependencies..." -ForegroundColor Yellow

$npmPackageJson = Join-Path $FrontendPath "package.json"
if (Test-Path $npmPackageJson) {
    Write-Host "  Running npm audit..." -ForegroundColor Gray
    try {
        $npmResult = & npm audit --json 2>&1 | Out-String
        $npmData = $npmResult | ConvertFrom-Json -ErrorAction SilentlyContinue

        if ($npmData.vulnerabilities) {
            foreach ($pkg in $npmData.vulnerabilities.PSObject.Properties) {
                $vulnInfo = $pkg.Value
                $severity = $vulnInfo.severity
                $severityMap = @{
                    "critical" = "Critical"
                    "high"     = "High"
                    "moderate" = "Medium"
                    "low"      = "Low"
                    "info"     = "Info"
                }
                $mappedSeverity = $severityMap[$severity.ToLower()]

                $fixVersion = ""
                if ($vulnInfo.fixAvailable -is [PSCustomObject]) {
                    $fixVersion = $vulnInfo.fixAvailable.version
                } elseif ($vulnInfo.fixAvailable -eq $true) {
                    $fixVersion = "Run 'npm audit fix'"
                }

                $advisory = ""
                $title = ""
                if ($vulnInfo.via -and $vulnInfo.via.Count -gt 0) {
                    $firstVia = $vulnInfo.via[0]
                    if ($firstVia -is [PSCustomObject]) {
                        $advisory = $firstVia.url
                        $title = $firstVia.title
                    } else {
                        $title = "Dependency of $firstVia"
                    }
                }

                Add-DepFinding -Ecosystem "npm" -Package $pkg.Name `
                    -InstalledVersion ($vulnInfo.range) `
                    -FixedVersion $fixVersion `
                    -Severity $mappedSeverity `
                    -Advisory $advisory `
                    -Title $title
            }

            $npmTotal = $npmData.metadata?.totalDependencies
            $npmVulns = $npmData.metadata?.vulnerabilities
            $criticalHigh = ($npmVulns?.critical ?? 0) + ($npmVulns?.high ?? 0)
            Write-Host "  npm: $criticalHigh critical/high vulnerabilities out of $npmTotal dependencies" -ForegroundColor $(if ($criticalHigh -gt 0) { "Red" } else { "Green" })
            Write-Host "    Critical: $($npmVulns?.critical ?? 0) | High: $($npmVulns?.high ?? 0) | Medium: $($npmVulns?.moderate ?? 0) | Low: $($npmVulns?.low ?? 0)" -ForegroundColor Gray
        } else {
            Write-Host "  npm audit: No vulnerabilities found" -ForegroundColor Green
        }
    } catch {
        Write-Host "  npm audit failed — $_" -ForegroundColor Red
    }
} else {
    Write-Host "  package.json not found at $npmPackageJson" -ForegroundColor Yellow
}

# ──────────────────────────────────────────────────────────────────────────
# GENERATE REPORT
# ──────────────────────────────────────────────────────────────────────────

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$criticalFindings = $findings | Where-Object { $_.Severity -eq "Critical" }
$highFindings = $findings | Where-Object { $_.Severity -eq "High" }

$report = [PSCustomObject]@{
    metadata = [PSCustomObject]@{
        tool       = "salesos-dep-scanner"
        version    = "1.0.0"
        timestamp  = (Get-Date -Format "o")
        duration_s = [math]::Round($duration, 2)
    }
    summary = [PSCustomObject]@{
        total_vulnerabilities = $findings.Count
        critical             = $criticalFindings.Count
        high                 = $highFindings.Count
        medium               = ($findings | Where-Object { $_.Severity -eq "Medium" }).Count
        low                  = ($findings | Where-Object { $_.Severity -eq "Low" }).Count
        needs_immediate_action = ($criticalFindings.Count -gt 0)
    }
    vulnerabilities = $findings
}

$report | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputPath -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " SCAN RESULTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Total vulnerabilities:  $($findings.Count)"
Write-Host " Critical:              $($criticalFindings.Count)" -ForegroundColor $(if ($criticalFindings.Count -gt 0) { "Red" } else { "Green" })
Write-Host " High:                  $($highFindings.Count)" -ForegroundColor $(if ($highFindings.Count -gt 0) { "Red" } else { "Green" })
Write-Host " Medium:                $(($findings | Where-Object { $_.Severity -eq 'Medium' }).Count)" -ForegroundColor Yellow
Write-Host " Low:                   $(($findings | Where-Object { $_.Severity -eq 'Low' }).Count)" -ForegroundColor Green
Write-Host " Duration:              ${duration}s"
Write-Host " Report:                $OutputPath"
Write-Host "============================================" -ForegroundColor Cyan

if ($criticalFindings.Count -gt 0) {
    Write-Host ""
    Write-Host "CRITICAL VULNERABILITIES — IMMEDIATE ACTION REQUIRED:" -ForegroundColor Red
    $criticalFindings | ForEach-Object {
        Write-Host "  [$($_.Ecosystem)] $($_.Package) ($($_.InstalledVersion))" -ForegroundColor Red
        Write-Host "    $($_.Title)" -ForegroundColor Gray
        if ($_.FixedVersion) {
            Write-Host "    Fix: upgrade to $($_.FixedVersion)" -ForegroundColor Yellow
        }
    }
}

if ($highFindings.Count -gt 0) {
    Write-Host ""
    Write-Host "HIGH VULNERABILITIES:" -ForegroundColor Yellow
    $highFindings | ForEach-Object {
        Write-Host "  [$($_.Ecosystem)] $($_.Package) ($($_.InstalledVersion))" -ForegroundColor Yellow
        if ($_.FixedVersion) {
            Write-Host "    Fix: upgrade to $($_.FixedVersion)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "REMEDIATION COMMANDS:" -ForegroundColor Cyan
Write-Host "  Python:  cd $BackendPath && pip install --upgrade <package>" -ForegroundColor Gray
Write-Host "  Frontend: cd $FrontendPath && npm audit fix" -ForegroundColor Gray
