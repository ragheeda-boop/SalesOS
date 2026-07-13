<#
.SYNOPSIS
    SalesOS Backup Verification Script — pg_dump, restore to temp DB, verify row counts and indexes.

.DESCRIPTION
    1. Runs pg_dump to a temp file
    2. Restores to a temporary database
    3. Verifies row counts match source tables
    4. Verifies all indexes exist in the restored database
    5. Reports pass/fail with details

.PARAMETER SourceDb
    Source database name (default: $env:DB_NAME or "salesos")

.PARAMETER SourceHost
    Source database host (default: $env:DB_HOST or "localhost")

.PARAMETER SourcePort
    Source database port (default: $env:DB_PORT or "5432")

.PARAMETER SourceUser
    Source database user (default: $env:DB_USER or "salesos")

.PARAMETER TempDbName
    Temporary database name for restore verification (default: "salesos_verify_tmp")

.EXAMPLE
    .\verify-backup.ps1
    .\verify-backup.ps1 -SourceDb salesos -SourceHost localhost -SourcePort 5432
#>
[CmdletBinding()]
param(
    [string]$SourceDb = $env:DB_NAME,
    [string]$SourceHost = $env:DB_HOST,
    [string]$SourcePort = $env:DB_PORT,
    [string]$SourceUser = $env:DB_USER,
    [string]$TempDbName = "salesos_verify_tmp"
)

$ErrorActionPreference = "Stop"

# Defaults
if (-not $SourceDb) { $SourceDb = "salesos" }
if (-not $SourceHost) { $SourceHost = "localhost" }
if (-not $SourcePort) { $SourcePort = "5432" }
if (-not $SourceUser) { $SourceUser = "salesos" }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$TempDumpFile = Join-Path $env:TEMP "salesos_verify_$Timestamp.dump"
$PassCount = 0
$FailCount = 0
$Details = @()

function Write-Status {
    param([string]$Message, [string]$Status)
    $color = switch ($Status) { "PASS" { "Green" } "FAIL" { "Red" } "INFO" { "Cyan" } default { "White" } }
    Write-Host "  [$Status] $Message" -ForegroundColor $color
}

function Invoke-Psql {
    param([string]$Db, [string]$Query)
    $env:PGPASSWORD = $env:DB_PASSWORD
    $result = & psql -h $SourceHost -p $SourcePort -U $SourceUser -d $Db -t -A -c $Query 2>&1
    if ($LASTEXITCODE -ne 0) { throw "psql error: $result" }
    return $result
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SalesOS Backup Verification" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: pg_dump ──────────────────────────────────────────────
Write-Host "[1/4] Running pg_dump from $SourceDb..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = $env:DB_PASSWORD
    & pg_dump -h $SourceHost -p $SourcePort -U $SourceUser -d $SourceDb --format=custom --compress=9 --file=$TempDumpFile 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $TempDumpFile)) {
        throw "pg_dump failed or output file missing"
    }
    $dumpSize = (Get-Item $TempDumpFile).Length / 1MB
    Write-Status "pg_dump completed: $([math]::Round($dumpSize, 2)) MB" "PASS"
    $PassCount++
    $Details += "pg_dump: OK ($([math]::Round($dumpSize, 2)) MB)"
}
catch {
    Write-Status "pg_dump failed: $_" "FAIL"
    $FailCount++
    $Details += "pg_dump: FAILED - $_"
    Write-Host ""
    Write-Host "Verification FAILED — cannot proceed without a valid dump." -ForegroundColor Red
    exit 1
}

# ── Step 2: Restore to temp database ─────────────────────────────
Write-Host ""
Write-Host "[2/4] Restoring to temp database '$TempDbName'..." -ForegroundColor Yellow
try {
    # Terminate existing connections to temp DB
    $env:PGPASSWORD = $env:DB_PASSWORD
    & psql -h $SourceHost -p $SourcePort -U $SourceUser -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$TempDbName' AND pid <> pg_backend_pid();" 2>&1 | Out-Null

    # Drop and recreate temp database
    & psql -h $SourceHost -p $SourcePort -U $SourceUser -d postgres -c "DROP DATABASE IF EXISTS $TempDbName;" 2>&1 | Out-Null
    & psql -h $SourceHost -p $SourcePort -U $SourceUser -d postgres -c "CREATE DATABASE $TempDbName OWNER $SourceUser;" 2>&1 | Out-Null

    # Restore
    & pg_restore -h $SourceHost -p $SourcePort -U $SourceUser -d $TempDbName --clean --if-exists --no-owner --no-acl $TempDumpFile 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "pg_restore returned non-zero exit code" }

    Write-Status "Restore to $TempDbName completed" "PASS"
    $PassCount++
    $Details += "Restore: OK"
}
catch {
    Write-Status "Restore failed: $_" "FAIL"
    $FailCount++
    $Details += "Restore: FAILED - $_"
}

# ── Step 3: Verify row counts ───────────────────────────────────
Write-Host ""
Write-Host "[3/4] Verifying row counts (source vs restored)..." -ForegroundColor Yellow
try {
    $tableQuery = @"
SELECT schemaname || '.' || tablename AS tbl
FROM pg_stat_user_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
"@
    $tables = (Invoke-Psql -Db $SourceDb -Query $tableQuery) -split "`n" | Where-Object { $_.Trim() }
    $mismatchCount = 0

    foreach ($tbl in $tables) {
        $tbl = $tbl.Trim()
        if (-not $tbl) { continue }

        $countQuery = "SELECT count(*) FROM $tbl;"
        $srcCount = ((Invoke-Psql -Db $SourceDb -Query $countQuery).Trim())
        $dstCount = ((Invoke-Psql -Db $TempDbName -Query $countQuery).Trim())

        if ($srcCount -eq $dstCount) {
            Write-Status "$tbl : $srcCount rows" "PASS"
            $PassCount++
        } else {
            Write-Status "$tbl : SOURCE=$srcCount RESTORED=$dstCount" "FAIL"
            $FailCount++
            $mismatchCount++
            $Details += "Row count mismatch: $tbl (source=$srcCount, restored=$dstCount)"
        }
    }

    if ($mismatchCount -eq 0) {
        Write-Status "All table row counts match" "PASS"
    } else {
        $Details += "$mismatchCount table(s) have row count mismatches"
    }
}
catch {
    Write-Status "Row count verification failed: $_" "FAIL"
    $FailCount++
    $Details += "Row count check: FAILED - $_"
}

# ── Step 4: Verify indexes ──────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Verifying indexes exist in restored database..." -ForegroundColor Yellow
try {
    $indexQuery = @"
SELECT schemaname || '.' || tablename || '.' || indexname AS idx
FROM pg_stat_user_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename, indexname;
"@
    $sourceIndexes = (Invoke-Psql -Db $SourceDb -Query $indexQuery) -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() }
    $restoredIndexes = (Invoke-Psql -Db $TempDbName -Query $indexQuery) -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() }

    $missingIndexes = @()
    foreach ($idx in $sourceIndexes) {
        if ($idx -notin $restoredIndexes) {
            $missingIndexes += $idx
        }
    }

    $validQuery = @"
SELECT indexrelname || ' (INVALID)' AS bad_idx
FROM pg_stat_user_indexes
JOIN pg_index ON indexrelid = pg_stat_user_indexes.indexrelid
WHERE NOT indisvalid;
"@
    $invalidIdx = (Invoke-Psql -Db $TempDbName -Query $validQuery) -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() }

    if ($missingIndexes.Count -eq 0 -and $invalidIdx.Count -eq 0) {
        Write-Status "All $($sourceIndexes.Count) indexes present and valid in restored DB" "PASS"
        $PassCount++
        $Details += "Indexes: OK ($($sourceIndexes.Count) total)"
    } else {
        foreach ($mi in $missingIndexes) {
            Write-Status "Missing index: $mi" "FAIL"
            $FailCount++
            $Details += "Missing index: $mi"
        }
        foreach ($ii in ($invalidIdx | Where-Object { $_ })) {
            Write-Status "Invalid index: $ii" "FAIL"
            $FailCount++
            $Details += "Invalid index: $ii"
        }
    }
}
catch {
    Write-Status "Index verification failed: $_" "FAIL"
    $FailCount++
    $Details += "Index check: FAILED - $_"
}

# ── Cleanup ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "Cleaning up temp database and dump file..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = $env:DB_PASSWORD
    & psql -h $SourceHost -p $SourcePort -U $SourceUser -d postgres -c "DROP DATABASE IF EXISTS $TempDbName;" 2>&1 | Out-Null
    if (Test-Path $TempDumpFile) { Remove-Item $TempDumpFile -Force }
    Write-Status "Cleanup complete" "INFO"
}
catch {
    Write-Host "  [WARN] Cleanup failed: $_" -ForegroundColor DarkYellow
}

# ── Neo4j Verification ─────────────────────────────────────────
Write-Host ""
Write-Host "=== Neo4j Backup Verification ===" -ForegroundColor Yellow
try {
    $neo4jContainer = & docker compose ps -q neo4j 2>&1
    if ($neo4jContainer) {
        $nodeCount = & docker compose exec -T neo4j cypher-shell -u neo4j -p "$($env:NEO4J_PASSWORD)" "MATCH (n) RETURN count(n) AS cnt" 2>&1
        if ($LASTEXITCODE -eq 0 -and $nodeCount -match "\d+") {
            Write-Status "Neo4j reachable: $nodeCount nodes" "PASS"
            $PassCount++
            $Details += "Neo4j: OK ($nodeCount nodes)"

            $relCount = & docker compose exec -T neo4j cypher-shell -u neo4j -p "$($env:NEO4J_PASSWORD)" "MATCH ()-[r]->() RETURN count(r) AS cnt" 2>&1
            if ($relCount -match "\d+") {
                Write-Status "Neo4j relationships: $relCount" "PASS"
                $PassCount++
                $Details += "Neo4j relationships: OK ($relCount)"
            }
        }
        else {
            Write-Status "Neo4j query failed" "FAIL"
            $FailCount++
            $Details += "Neo4j: FAILED - cypher-shell query error"
        }
    }
    else {
        Write-Status "Neo4j container not running — skipped" "INFO"
    }
}
catch {
    Write-Status "Neo4j verification failed: $_" "FAIL"
    $FailCount++
    $Details += "Neo4j verification: FAILED - $_"
}

# ── Summary ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Pass: $PassCount" -ForegroundColor Green
Write-Host "  Fail: $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Status: $(if ($FailCount -eq 0) { 'ALL PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($FailCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($FailCount -gt 0) {
    Write-Host "Failed checks:" -ForegroundColor Red
    foreach ($d in $Details | Where-Object { $_ -match "FAIL|Mismatch|Missing|Invalid" }) {
        Write-Host "  - $d" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
} else {
    Write-Host "All backup verification checks passed." -ForegroundColor Green
    exit 0
}
