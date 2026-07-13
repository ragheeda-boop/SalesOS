<#
.SYNOPSIS
    Neo4j Recovery Procedure for SalesOS.

.DESCRIPTION
    Recovers Neo4j from a backup dump file.
    Steps:
      1. Stop Neo4j
      2. Remove existing data
      3. Load the dump file via neo4j-admin database load
      4. Start Neo4j
      5. Verify recovery

.PARAMETER DumpFile
    Path to the .dump file to restore from.

.EXAMPLE
    .\neo4j-recover.ps1 -DumpFile ".\backups\neo4j\neo4j_dump_20260713_030000.dump"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DumpFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $DumpFile)) {
    Write-Host "ERROR: Dump file not found: $DumpFile" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Neo4j Recovery — SalesOS" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dump file: $DumpFile" -ForegroundColor Yellow
Write-Host "  Size: $([math]::Round((Get-Item $DumpFile).Length / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host ""

# ── Step 1: Confirm ──
Write-Host "  WARNING: This will REPLACE all existing Neo4j data." -ForegroundColor Red
$confirm = Read-Host "  Type 'YES' to continue"
if ($confirm -ne "YES") {
    Write-Host "  Aborted." -ForegroundColor Yellow
    exit 0
}

# ── Step 2: Stop Neo4j ──
Write-Host "[1/5] Stopping Neo4j..." -ForegroundColor Yellow
docker compose stop neo4j 2>&1 | Out-Null
Start-Sleep -Seconds 5
Write-Host "  Neo4j stopped" -ForegroundColor Green

# ── Step 3: Clear existing data ──
Write-Host "[2/5] Clearing existing Neo4j data..." -ForegroundColor Yellow
$container = docker compose ps -q neo4j 2>&1
& docker volume rm salesos_neo4j_data 2>&1 | Out-Null
Write-Host "  Data volume removed" -ForegroundColor Green

# ── Step 4: Start Neo4j and load dump ──
Write-Host "[3/5] Starting Neo4j and loading dump..." -ForegroundColor Yellow
docker compose up -d neo4j 2>&1 | Out-Null

$timeout = 90
$elapsed = 0
while ($elapsed -lt $timeout) {
    $status = docker compose ps neo4j --format '{{.Status}}' 2>&1
    if ($status -match "healthy|Up") { break }
    Start-Sleep -Seconds 5
    $elapsed += 5
}

$container = docker compose ps -q neo4j 2>&1
& docker cp "$DumpFile" "${container}:/tmp/neo4j_restore.dump" 2>&1

$loadResult = & docker exec $container neo4j-admin database load neo4j --from-path="/tmp/neo4j_restore.dump" --overwrite-destination 2>&1
& docker exec $container rm -f /tmp/neo4j_restore.dump 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: neo4j-admin load failed: $loadResult" -ForegroundColor Red
    Write-Host "  Attempting restart with existing data..." -ForegroundColor Yellow
    docker compose restart neo4j 2>&1 | Out-Null
    exit 1
}

Write-Host "  Dump loaded successfully" -ForegroundColor Green

# ── Step 5: Restart Neo4j ──
Write-Host "[4/5] Restarting Neo4j..." -ForegroundColor Yellow
docker compose restart neo4j 2>&1 | Out-Null
$elapsed = 0
while ($elapsed -lt $timeout) {
    $status = docker compose ps neo4j --format '{{.Status}}' 2>&1
    if ($status -match "healthy|Up") { break }
    Start-Sleep -Seconds 5
    $elapsed += 5
}
Write-Host "  Neo4j restarted" -ForegroundColor Green

# ── Step 6: Verify ──
Write-Host "[5/5] Verifying recovery..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$env:NEO4J_PASSWORD = $env:NEO4J_PASSWORD
$verifyResult = & docker compose exec -T neo4j cypher-shell -u neo4j -p "$($env:NEO4J_PASSWORD)" "MATCH (n) RETURN count(n) AS nodeCount" 2>&1

if ($verifyResult -match "\d+") {
    Write-Host "  Verification passed: $verifyResult" -ForegroundColor Green
}
else {
    Write-Host "  WARNING: Verification could not confirm data: $verifyResult" -ForegroundColor Yellow
}

# ── Summary ──
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  RECOVERY COMPLETE" -ForegroundColor Green
Write-Host "  Restored from: $DumpFile" -ForegroundColor Cyan
Write-Host "  Node count: $verifyResult" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
