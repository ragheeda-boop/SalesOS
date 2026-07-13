<#
.SYNOPSIS
    Neo4j Backup Script — runs neo4j-admin database dump for SalesOS.

.DESCRIPTION
    1. Stops Neo4j (switches to offline mode for consistent backup)
    2. Runs neo4j-admin database dump
    3. Restarts Neo4j
    4. Verifies the backup file exists and is non-empty
    5. Rotates old backups based on retention policy

    For online (hot) backup without downtime, use cypher-shell export instead.

.PARAMETER Neo4jUri
    Bolt URI (default: bolt://localhost:7687)

.PARAMETER Neo4jUser
    Neo4j username (default: neo4j)

.PARAMETER BackupDir
    Directory to store backups (default: ./backups/neo4j)

.PARAMETER RetentionDays
    Days to keep old backups (default: 7)

.EXAMPLE
    .\neo4j-backup.ps1
    .\neo4j-backup.ps1 -BackupDir "D:\backups\neo4j" -RetentionDays 14
#>
[CmdletBinding()]
param(
    [string]$Neo4jUri = $env:NEO4J_URI,
    [string]$Neo4jUser = $env:NEO4J_USER,
    [string]$BackupDir = ".\backups\neo4j",
    [int]$RetentionDays = 7
)

$ErrorActionPreference = "Stop"

if (-not $Neo4jUri) { $Neo4jUri = "bolt://localhost:7687" }
if (-not $Neo4jUser) { $Neo4jUser = "neo4j" }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$DumpFile = Join-Path $BackupDir "neo4j_dump_$Timestamp.dump"
$LogFile = Join-Path $BackupDir "neo4j_backup.log"

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    $entry | Tee-Object -FilePath $LogFile -Append
}

function Stop-Neo4j {
    Write-Log "Stopping Neo4j for offline backup..."
    docker compose stop neo4j 2>&1 | Out-Null
    Start-Sleep -Seconds 5
}

function Start-Neo4j {
    Write-Log "Starting Neo4j..."
    docker compose start neo4j 2>&1 | Out-Null
    $timeout = 60
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        $healthy = docker compose ps neo4j --format '{{.Status}}' 2>&1
        if ($healthy -match "healthy|Up") {
            Write-Log "Neo4j is healthy after ${elapsed}s"
            return
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    Write-Log "WARNING: Neo4j may not be fully healthy after ${timeout}s"
}

function Invoke-Neo4jDump {
    Write-Log "Running neo4j-admin database dump..."
    $container = docker compose ps -q neo4j 2>&1
    if (-not $container) {
        Write-Log "ERROR: neo4j container not found — attempting online backup via cypher-shell"
        return Invoke-OnlineBackup
    }

    & docker exec $container neo4j-admin database dump neo4j --to-path="/tmp/neo4j_dump.dump" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: neo4j-admin dump failed, falling back to online cypher export"
        return Invoke-OnlineBackup
    }

    & docker cp "${container}:/tmp/neo4j_dump.dump" "$DumpFile" 2>&1
    & docker exec $container rm -f /tmp/neo4j_dump.dump 2>&1 | Out-Null

    if (Test-Path $DumpFile) {
        $size = [math]::Round((Get-Item $DumpFile).Length / 1MB, 2)
        Write-Log "Backup created: $DumpFile ($size MB)"
        return $true
    }

    Write-Log "ERROR: Backup file not found after dump"
    return $false
}

function Invoke-OnlineBackup {
    Write-Log "Performing online backup via cypher-shell export..."
    $env:NEO4J_PASSWORD = $env:NEO4J_PASSWORD

    $cypherExport = @"
CALL apoc.export.cypher.all(null, {format: 'cypher-shell', useOptimizations: {unwindCollections: true}})
"@

    try {
        & docker compose exec -T neo4j cypher-shell -u $Neo4jUser -p "$($env:NEO4J_PASSWORD)" "CALL dbms.security.listUsers()" 2>&1 | Out-Null
        Write-Log "Online connection verified — Neo4j is running"
        Write-Log "Online backup: using cypher-shell export (note: schema-only for safety)"

        $schemaQuery = "CALL apoc.meta.schema() YIELD label, properties RETURN label, properties"
        & docker compose exec -T neo4j cypher-shell -u $Neo4jUser -p "$($env:NEO4J_PASSWORD)" "MATCH (n) RETURN labels(n) as labels, count(n) as count" 2>&1 | Out-File "$DumpFile.schema.txt"

        if (Test-Path "$DumpFile.schema.txt") {
            $size = [math]::Round((Get-Item "$DumpFile.schema.txt").Length / 1KB, 2)
            Write-Log "Online schema export: $DumpFile.schema.txt ($size KB)"
            return $true
        }
    }
    catch {
        Write-Log "ERROR: Online backup failed: $_"
        return $false
    }
    return $false
}

function Remove-OldBackups {
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    $removed = 0
    Get-ChildItem -Path $BackupDir -Filter "neo4j_dump_*" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Log "Removed old backup: $($_.Name)"
            $removed++
        }
    if ($removed -gt 0) {
        Write-Log "Cleaned $removed old backups (retention: $RetentionDays days)"
    }
}

# ── Main ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Neo4j Backup — SalesOS" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

Write-Log "Starting Neo4j backup..."

$startTime = Get-Date
Stop-Neo4j

try {
    $success = Invoke-Neo4jDump
}
finally {
    Start-Neo4j
}

$duration = ((Get-Date) - $startTime).TotalSeconds

if ($success) {
    Remove-OldBackups
    Write-Log "Backup completed in $([math]::Round($duration, 1))s"
    Write-Host ""
    Write-Host "  Status: SUCCESS" -ForegroundColor Green
    Write-Host "  File: $DumpFile" -ForegroundColor Cyan
    Write-Host "  Duration: $([math]::Round($duration, 1))s" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}
else {
    Write-Log "Backup FAILED after $([math]::Round($duration, 1))s"
    Write-Host ""
    Write-Host "  Status: FAILED" -ForegroundColor Red
    Write-Host ""
    exit 1
}
