<#
.SYNOPSIS
    SalesOS Alembic Migration Audit Script — lists migrations, checks downgrades, finds duplicates.

.DESCRIPTION
    1. Lists all migration files with revision IDs
    2. Checks each has a downgrade() function implemented
    3. Identifies duplicate revision IDs
    4. Identifies broken chain links (missing down_revision references)
    5. Reports pass/fail with details

.PARAMETER MigrationsDir
    Path to the Alembic versions directory (default: auto-detected)

.EXAMPLE
    .\audit-migrations.ps1
    .\audit-migrations.ps1 -MigrationsDir "C:\path\to\versions"
#>
[CmdletBinding()]
param(
    [string]$MigrationsDir
)

$ErrorActionPreference = "Stop"

# Auto-detect migrations directory
if (-not $MigrationsDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $MigrationsDir = Join-Path (Split-Path -Parent $scriptDir) "backend\app\alembic\versions"
}

if (-not (Test-Path $MigrationsDir)) {
    Write-Host "ERROR: Migrations directory not found: $MigrationsDir" -ForegroundColor Red
    exit 1
}

$PassCount = 0
$FailCount = 0
$WarnCount = 0
$Details = @()
$RevisionMap = @{}
$ChainIssues = @()

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Alembic Migration Audit" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Scanning: $MigrationsDir" -ForegroundColor Gray
Write-Host ""

# ── Step 1: Parse all migration files ────────────────────────────
Write-Host "[1/4] Parsing migration files..." -ForegroundColor Yellow

$migrationFiles = Get-ChildItem -Path $MigrationsDir -Filter "*.py" | Sort-Object Name
$allMigrations = @()

foreach ($file in $migrationFiles) {
    $content = Get-Content -Path $file.FullName -Raw

    # Extract revision ID
    $revMatch = [regex]::Match($content, 'revision\s*:\s*str\s*=\s*"([^"]+)"')
    if (-not $revMatch.Success) {
        $revMatch = [regex]::Match($content, 'revision\s*=\s*"([^"]+)"')
    }

    # Extract down_revision
    $downMatch = [regex]::Match($content, 'down_revision\s*:\s*Union\[str,\s*None\]\s*=\s*"([^"]+)"')
    if (-not $downMatch.Success) {
        $downMatch = [regex]::Match($content, 'down_revision\s*=\s*"([^"]+)"')
    }

    # Check for None down_revision (baseline)
    $isNoneDown = $content -match 'down_revision\s*=\s*None' -or $content -match 'down_revision\s*:\s*Union\[str,\s*None\]\s*=\s*None'

    # Check for downgrade() function
    $hasDowngrade = $content -match 'def\s+downgrade\s*\(\s*\)'

    $rev = if ($revMatch.Success) { $revMatch.Groups[1].Value } else { "UNKNOWN" }
    $downRev = if ($downMatch.Success) { $downMatch.Groups[1].Value } elseif ($isNoneDown) { "None" } else { "UNKNOWN" }

    # Extract docstring description (first line after triple quotes)
    $descMatch = [regex]::Match($content, '"""([^""]+)')
    $description = if ($descMatch.Success) { $descMatch.Groups[1].Value.Substring(0, [Math]::Min(80, $descMatch.Groups[1].Value.Length)) } else { "(no description)" }

    $allMigrations += [PSCustomObject]@{
        File = $file.Name
        Revision = $rev
        DownRevision = $downRev
        HasDowngrade = $hasDowngrade
        Description = $description
    }

    # Build revision map
    if ($RevisionMap.ContainsKey($rev)) {
        $RevisionMap[$rev] += $file.Name
    } else {
        $RevisionMap[$rev] = @($file.Name)
    }
}

Write-Host "  Found $($allMigrations.Count) migration files" -ForegroundColor White

# ── Step 2: Check for duplicate revision IDs ─────────────────────
Write-Host ""
Write-Host "[2/4] Checking for duplicate revision IDs..." -ForegroundColor Yellow

$hasDuplicates = $false
foreach ($rev in $RevisionMap.Keys | Sort-Object) {
    $files = $RevisionMap[$rev]
    if ($files.Count -gt 1) {
        Write-Host "  [FAIL] Duplicate revision '$rev' in files:" -ForegroundColor Red
        foreach ($f in $files) {
            Write-Host "         - $f" -ForegroundColor Red
        }
        $FailCount++
        $hasDuplicates = $true
        $Details += "Duplicate revision ID '$rev': $($files -join ', ')"
    }
}

if (-not $hasDuplicates) {
    Write-Host "  [PASS] No duplicate revision IDs found" -ForegroundColor Green
    $PassCount++
}

# ── Step 3: Check downgrade() implementations ────────────────────
Write-Host ""
Write-Host "[3/4] Checking downgrade() implementations..." -ForegroundColor Yellow

$missingDowngrades = @()
foreach ($m in $allMigrations) {
    if (-not $m.HasDowngrade) {
        Write-Host "  [FAIL] Missing downgrade(): $($m.File) (rev: $($m.Revision))" -ForegroundColor Red
        $missingDowngrades += $m
        $FailCount++
        $Details += "Missing downgrade(): $($m.File)"
    }
}

if ($missingDowngrades.Count -eq 0) {
    Write-Host "  [PASS] All migrations have downgrade() implemented" -ForegroundColor Green
    $PassCount++
}

# ── Step 4: Check chain integrity ────────────────────────────────
Write-Host ""
Write-Host "[4/4] Checking migration chain integrity..." -ForegroundColor Yellow

$knownRevisions = $RevisionMap.Keys
$chainIssues = @()

foreach ($m in $allMigrations) {
    if ($m.DownRevision -eq "None") {
        # Baseline — expected
        continue
    }

    if ($m.DownRevision -notin $knownRevisions) {
        Write-Host "  [FAIL] $($m.File): references unknown down_revision '$($m.DownRevision)'" -ForegroundColor Red
        $chainIssues += "$($m.File) -> $($m.DownRevision) (NOT FOUND)"
        $FailCount++
        $Details += "Broken chain: $($m.File) references missing revision '$($m.DownRevision)'"
    }
}

if ($chainIssues.Count -eq 0) {
    Write-Host "  [PASS] Migration chain is intact" -ForegroundColor Green
    $PassCount++
}

# ── Summary ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AUDIT SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total migrations:     $($allMigrations.Count)" -ForegroundColor White
Write-Host "  Pass:                 $PassCount" -ForegroundColor Green
Write-Host "  Fail:                 $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Status:               $(if ($FailCount -eq 0) { 'ALL PASSED' } else { 'ISSUES FOUND' })" -ForegroundColor $(if ($FailCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

# ── Migration List ──────────────────────────────────────────────
Write-Host "  Migration Chain:" -ForegroundColor Cyan
Write-Host "  " + ("=" * 60) -ForegroundColor Gray
foreach ($m in ($allMigrations | Sort-Object Revision)) {
    $downDisplay = if ($m.DownRevision -eq "None") { "NULL" } else { $m.DownRevision }
    $dgIcon = if ($m.HasDowngrade) { "[DG]" } else { "[NO DG]" }
    $dgColor = if ($m.HasDowngrade) { "Green" } else { "Red" }
    Write-Host ("  {0,-6} <- {1,-6}  {2,-8} {3}" -f $m.Revision, $downDisplay, $dgIcon, $m.File) -ForegroundColor $dgColor
}
Write-Host ""

if ($FailCount -gt 0) {
    Write-Host "Issues:" -ForegroundColor Red
    foreach ($d in $Details) {
        Write-Host "  - $d" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
} else {
    Write-Host "All migration audit checks passed." -ForegroundColor Green
    exit 0
}
