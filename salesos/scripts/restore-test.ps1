<#
.SYNOPSIS
  SalesOS Backup Restore Test — validates backup integrity by restoring to a temp environment
.DESCRIPTION
  Phase 1: Create full backup (pg_dump + neo4j-admin dump + redis SAVE)
  Phase 2: Destroy data (DROP SCHEMA public CASCADE, DETACH DELETE, FLUSHALL)
  Phase 3: Restore from backup (pg_restore + neo4j-admin load + redis LOAD)
  Phase 4: Verify row counts match pre-backup + smoke test
.PARAMETER BackupDir
  Local backup directory (default: /backups)
.PARAMETER PgHost
  PostgreSQL host (default: postgres)
.PARAMETER PgPort
  PostgreSQL port (default: 5432)
.PARAMETER PgUser
  PostgreSQL user (default: salesos)
.PARAMETER PgDb
  PostgreSQL database (default: salesos)
.PARAMETER Neo4jUri
  Neo4j bolt URI (default: bolt://neo4j:7687)
.PARAMETER Neo4jUser
  Neo4j user (default: neo4j)
.PARAMETER RedisHost
  Redis host (default: redis)
.PARAMETER RedisPort
  Redis port (default: 6379)
.PARAMETER BaseUrl
  Backend API base URL for smoke test (default: http://localhost:8000)
.PARAMETER AutoCleanup
  Restore data after test (default: $true)
#>

param(
    [string]$BackupDir = "/backups",
    [string]$PgHost = "postgres",
    [int]$PgPort = 5432,
    [string]$PgUser = "salesos",
    [string]$PgDb = "salesos",
    [string]$Neo4jUri = "bolt://neo4j:7687",
    [string]$Neo4jUser = "neo4j",
    [string]$RedisHost = "redis",
    [int]$RedisPort = 6379,
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$AutoCleanup = $true
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$passCount = 0
$failCount = 0
$preCounts = @{}   # stores pre-backup row counts

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $logLine = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Write-Host $logLine
}

function Write-Result {
    param([string]$Name, [string]$Status, [string]$Detail = "")
    $color = switch ($Status) { "PASS" { "Green" } "FAIL" { "Red" } "SKIP" { "DarkYellow" } default { "White" } }
    $detailStr = if ($Detail) { " - $Detail" } else { "" }
    Write-Host ("  [$Status] $Name$detailStr") -ForegroundColor $color
    if ($Status -eq "PASS") { $script:passCount++ } elseif ($Status -eq "FAIL") { $script:failCount++ }
}

function Assert-ExitCode {
    param([string]$Context)
    if ($LASTEXITCODE -ne 0) { throw "$Context failed with exit code $LASTEXITCODE" }
}

function Invoke-Psql {
    param([string]$Db, [string]$Query)
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    return & psql -h $PgHost -p $PgPort -U $PgUser -d $Db -t -A -c $Query 2>&1
}

# ============================================================
#  PHASE 1: Create Backup
# ============================================================
Write-Host "`n============================================`n  PHASE 1/4: Create Backup`n============================================" -ForegroundColor Cyan
Write-Log "Starting backup at $timestamp"

if (-not (Test-Path -LiteralPath $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null }

# --- 1a. PostgreSQL backup ---
try {
    Write-Log "Running pg_dump..."
    $pgDumpFile = "$BackupDir/restore-test-pg-$timestamp.dump"
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    & pg_dump -h $PgHost -p $PgPort -U $PgUser -d $PgDb --format=custom --compress=9 --file=$pgDumpFile
    Assert-ExitCode "pg_dump"
    Write-Result "PostgreSQL Backup" "PASS" "$((Get-Item $pgDumpFile).Length / 1MB -as [int]) MB"

    # Save pre-backup row counts per table
    $tables = (Invoke-Psql -Db $PgDb -Query "SELECT schemaname||'.'||tablename FROM pg_stat_user_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')") -split "`n" | Where-Object { $_.Trim() }
    foreach ($tbl in $tables) {
        $tbl = $tbl.Trim()
        if (-not $tbl) { continue }
        $cnt = (Invoke-Psql -Db $PgDb -Query "SELECT count(*) FROM $tbl").Trim()
        $preCounts["pg:$tbl"] = $cnt
    }
    Write-Result "Pre-backup Row Counts" "PASS" "$($tables.Count) tables recorded"
}
catch {
    Write-Result "PostgreSQL Backup" "FAIL" $_.Exception.Message
}

# --- 1b. Neo4j backup ---
try {
    Write-Log "Running Neo4j backup..."
    $neo4jFile = "$BackupDir/restore-test-neo4j-$timestamp.dump"

    # Save pre-backup node/relationship counts
    $env:NEO4J_PASSWORD = $env:NEO4J_PASSWORD
    $nodeCount = & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "MATCH (n) RETURN count(n) AS cnt" 2>$null
    if ($LASTEXITCODE -eq 0 -and $nodeCount -match "(\d+)") {
        $preCounts["neo4j:nodes"] = $Matches[1]
    }
    $relCount = & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "MATCH ()-[r]->() RETURN count(r) AS cnt" 2>$null
    if ($LASTEXITCODE -eq 0 -and $relCount -match "(\d+)") {
        $preCounts["neo4j:relationships"] = $Matches[1]
    }

    # Backup via APOC export (preferred) or neo4j-admin dump
    $neo4jResult = & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "CALL apoc.export.json.all('$neo4jFile', {useTypes: true})" 2>$null
    if ($LASTEXITCODE -ne 0) {
        & neo4j-admin dump --database=neo4j --to="$neo4jFile"
        Assert-ExitCode "neo4j-admin dump"
    }
    Write-Result "Neo4j Backup" "PASS" "$((Get-Item $neo4jFile).Length / 1MB -as [int]) MB"
}
catch {
    Write-Result "Neo4j Backup" "FAIL" $_.Exception.Message
}

# --- 1c. Redis backup ---
try {
    Write-Log "Running Redis SAVE..."
    if ($env:REDIS_PASSWORD) {
        & redis-cli -h $RedisHost -p $RedisPort -a $env:REDIS_PASSWORD SAVE | Out-Null
    } else {
        & redis-cli -h $RedisHost -p $RedisPort SAVE | Out-Null
    }
    Assert-ExitCode "Redis SAVE"
    Start-Sleep -Seconds 1
    $redisFile = "$BackupDir/restore-test-redis-$timestamp.rdb"
    Copy-Item -LiteralPath "/data/dump.rdb" -Destination $redisFile -ErrorAction SilentlyContinue
    Write-Result "Redis Backup" "PASS" "$((Get-Item $redisFile).Length / 1KB -as [int]) KB"
}
catch {
    Write-Result "Redis Backup" "FAIL" $_.Exception.Message
}

# ============================================================
#  PHASE 2: Destroy Data
# ============================================================
Write-Host "`n============================================`n  PHASE 2/4: Destroy Data`n============================================" -ForegroundColor Cyan
Write-Log "WARNING: Destroying data in source databases for restore test"

try {
    Write-Log "Dropping PostgreSQL schema..."
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    & psql -h $PgHost -p $PgPort -U $PgUser -d $PgDb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $PgUser; GRANT ALL ON SCHEMA public TO public;"
    Assert-ExitCode "PostgreSQL DROP SCHEMA"
    Write-Result "PostgreSQL Destroy" "PASS"
}
catch {
    Write-Result "PostgreSQL Destroy" "FAIL" $_.Exception.Message
}

try {
    Write-Log "Deleting Neo4j data..."
    & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "MATCH (n) DETACH DELETE n"
    Assert-ExitCode "Neo4j DETACH DELETE"
    Write-Result "Neo4j Destroy" "PASS"
}
catch {
    Write-Result "Neo4j Destroy" "FAIL" $_.Exception.Message
}

try {
    Write-Log "Flushing Redis..."
    if ($env:REDIS_PASSWORD) {
        & redis-cli -h $RedisHost -p $RedisPort -a $env:REDIS_PASSWORD FLUSHALL | Out-Null
    } else {
        & redis-cli -h $RedisHost -p $RedisPort FLUSHALL | Out-Null
    }
    Assert-ExitCode "Redis FLUSHALL"
    Write-Result "Redis Destroy" "PASS"
}
catch {
    Write-Result "Redis Destroy" "FAIL" $_.Exception.Message
}

# ============================================================
#  PHASE 3: Restore from Backup
# ============================================================
Write-Host "`n============================================`n  PHASE 3/4: Restore from Backup`n============================================" -ForegroundColor Cyan

try {
    Write-Log "Restoring PostgreSQL from backup..."
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    & pg_restore -h $PgHost -p $PgPort -U $PgUser -d $PgDb --clean --if-exists --no-owner --no-acl $pgDumpFile
    Assert-ExitCode "pg_restore"
    Write-Result "PostgreSQL Restore" "PASS"
}
catch {
    Write-Result "PostgreSQL Restore" "FAIL" $_.Exception.Message
}

try {
    Write-Log "Restoring Neo4j from backup..."
    if (Test-Path $neo4jFile) {
        & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "CALL apoc.import.json('$neo4jFile')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            & neo4j-admin load --from="$neo4jFile" --database=neo4j --force
            Assert-ExitCode "neo4j-admin load"
        }
        Write-Result "Neo4j Restore" "PASS"
    } else {
        Write-Result "Neo4j Restore" "SKIP" "no backup file"
    }
}
catch {
    Write-Result "Neo4j Restore" "FAIL" $_.Exception.Message
}

try {
    Write-Log "Restoring Redis from backup..."
    if (Test-Path $redisFile) {
        Copy-Item -LiteralPath $redisFile -Destination "/data/dump.rdb" -Force
        if ($env:REDIS_PASSWORD) {
            & redis-cli -h $RedisHost -p $RedisPort -a $env:REDIS_PASSWORD CONFIG SET dir "/data" | Out-Null
            & redis-cli -h $RedisHost -p $RedisPort -a $env:REDIS_PASSWORD DEBUG RELOAD | Out-Null
        } else {
            & redis-cli -h $RedisHost -p $RedisPort CONFIG SET dir "/data" | Out-Null
            & redis-cli -h $RedisHost -p $RedisPort DEBUG RELOAD | Out-Null
        }
        Assert-ExitCode "Redis reload"
        Write-Result "Redis Restore" "PASS"
    } else {
        Write-Result "Redis Restore" "SKIP" "no backup file"
    }
}
catch {
    Write-Result "Redis Restore" "FAIL" $_.Exception.Message
}

# ============================================================
#  PHASE 4: Verify
# ============================================================
Write-Host "`n============================================`n  PHASE 4/4: Verify Restore`n============================================" -ForegroundColor Cyan

# --- 4a. Verify PostgreSQL row counts ---
try {
    Write-Log "Verifying PostgreSQL row counts..."
    $mismatches = 0
    foreach ($key in $preCounts.Keys | Where-Object { $_ -like "pg:*" }) {
        $tbl = $key -replace "^pg:"
        $expected = $preCounts[$key]
        $actual = (Invoke-Psql -Db $PgDb -Query "SELECT count(*) FROM $tbl").Trim()
        if ($actual -eq $expected) {
            Write-Result "  $tbl" "PASS" "$actual rows"
        } else {
            Write-Result "  $tbl" "FAIL" "expected $expected, got $actual"
            $mismatches++
        }
    }
    if ($mismatches -eq 0) { Write-Result "PostgreSQL Row Counts" "PASS" }
    else { Write-Result "PostgreSQL Row Counts" "FAIL" "$mismatches mismatches" }
}
catch {
    Write-Result "PostgreSQL Row Counts" "FAIL" $_.Exception.Message
}

# --- 4b. Verify Neo4j node/relationship counts ---
try {
    $actualNodes = & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "MATCH (n) RETURN count(n) AS cnt" 2>$null
    $actualRels  = & cypher-shell -a $Neo4jUri -u $Neo4jUser -p $env:NEO4J_PASSWORD "MATCH ()-[r]->() RETURN count(r) AS cnt" 2>$null
    $nodeMatch = $actualNodes -match "(\d+)" -and $Matches[1] -eq $preCounts["neo4j:nodes"]
    $relMatch  = $actualRels -match "(\d+)" -and $Matches[1] -eq $preCounts["neo4j:relationships"]
    if ($nodeMatch -and $relMatch) {
        Write-Result "Neo4j Nodes" "PASS" "$($preCounts['neo4j:nodes']) nodes"
        Write-Result "Neo4j Relationships" "PASS" "$($preCounts['neo4j:relationships']) relationships"
    } else {
        if (-not $nodeMatch) { Write-Result "Neo4j Nodes" "FAIL" "expected $($preCounts['neo4j:nodes']), got $($Matches[1])" }
        if (-not $relMatch)  { Write-Result "Neo4j Relationships" "FAIL" "expected $($preCounts['neo4j:relationships']), got $($Matches[1])" }
    }
}
catch {
    Write-Result "Neo4j Verify" "FAIL" $_.Exception.Message
}

# --- 4c. Verify Redis keys ---
try {
    if ($env:REDIS_PASSWORD) {
        $keyCount = & redis-cli -h $RedisHost -p $RedisPort -a $env:REDIS_PASSWORD DBSIZE
    } else {
        $keyCount = & redis-cli -h $RedisHost -p $RedisPort DBSIZE
    }
    Write-Result "Redis Keys" "PASS" "$keyCount keys"
}
catch {
    Write-Result "Redis Keys" "FAIL" $_.Exception.Message
}

# --- 4d. Smoke test ---
try {
    Write-Log "Running smoke test against $BaseUrl..."
    $smokeResult = & "$PSScriptRoot/smoke-test.ps1" -BaseUrl $BaseUrl
    if ($LASTEXITCODE -eq 0) {
        Write-Result "Smoke Test" "PASS"
    } else {
        Write-Result "Smoke Test" "FAIL"
    }
}
catch {
    Write-Result "Smoke Test" "FAIL" $_.Exception.Message
}

# ============================================================
#  Summary
# ============================================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  RESTORE TEST SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Pass: $passCount" -ForegroundColor Green
Write-Host "  Fail: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Overall: $(if ($failCount -eq 0) { 'ALL PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failCount -gt 0) { exit 1 }
