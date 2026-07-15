<#
.SYNOPSIS
  SalesOS Production Backup — PostgreSQL, Neo4j, Redis
.DESCRIPTION
  Runs full backup of all databases, uploads to S3-compatible storage,
  and rotates old backups.
.PARAMETER BackupDir
  Local backup directory (default: /backups)
.PARAMETER RetentionDays
  Number of days to retain local backups (default: 7)
.PARAMETER S3Bucket
  S3 bucket name for offsite backup (default: salesos-backups)
.PARAMETER S3Endpoint
  S3 endpoint URL (default: https://s3.amazonaws.com)
.PARAMETER Upload
  Upload backups to S3 after dump
.PARAMETER SlackWebhook
  Slack webhook URL for notifications
#>

param(
    [string]$BackupDir = "/backups",
    [int]$RetentionDays = 7,
    [string]$S3Bucket = "salesos-backups",
    [string]$S3Endpoint = "https://s3.amazonaws.com",
    [switch]$Upload,
    [string]$SlackWebhook = ""
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$date = Get-Date -Format "yyyyMMdd"
$success = $true
$backupFiles = @()

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $logLine = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Write-Host $logLine
    $logLine | Out-File -FilePath "$BackupDir/backup.log" -Append -Encoding UTF8
}

function Send-Notification {
    param([string]$Status, [string]$Details)
    if (-not $SlackWebhook) { return }
    $body = @{
        channel = "#salesos-backups"
        username = "Backup Bot"
        icon_emoji = if ($Status -eq "SUCCESS") { ":white_check_mark:" } else { ":x:" }
        text = "SalesOS Backup $Status`n$Details"
    } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri $SlackWebhook -Method POST -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue
    } catch {
        Write-Log "Failed to send Slack notification: $_" "WARN"
    }
}

# Ensure backup directory exists
if (-not (Test-Path -LiteralPath $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Log "Starting SalesOS backup — $timestamp"
Write-Log "Backup directory: $BackupDir"
Write-Log "Retention: $RetentionDays days"

# ───────────────────────────────────────
# PostgreSQL Backup
# ───────────────────────────────────────
try {
    Write-Log "Starting PostgreSQL backup..."
    $pgFile = "$BackupDir/postgres-$date-$timestamp.sql.gz"
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD

    $pgDumpArgs = @(
        "-h", ($env:PGHOST -or "postgres"),
        "-U", ($env:PGUSER -or "salesos"),
        "-d", ($env:PGDATABASE -or "salesos"),
        "--no-owner",
        "--no-acl",
        "--verbose"
    )
    & pg_dump @pgDumpArgs | gzip > $pgFile

    if ($LASTEXITCODE -eq 0 -and (Test-Path $pgFile)) {
        $size = [math]::Round((Get-Item $pgFile).Length / 1MB, 2)
        Write-Log "PostgreSQL backup completed: ${size}MB" "SUCCESS"
        $backupFiles += $pgFile
    } else {
        throw "pg_dump failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Log "PostgreSQL backup FAILED: $_" "ERROR"
    $success = $false
}

# ───────────────────────────────────────
# Neo4j Backup
# ───────────────────────────────────────
try {
    Write-Log "Starting Neo4j backup..."

    # Try neo4j-admin dump (K8s/Docker)
    $neo4jFile = "$BackupDir/neo4j-$date-$timestamp.dump"

    # Attempt online backup via cypher-shell
    $neo4jResult = & cypher-shell `
        -a ($env:NEO4J_URI -or "bolt://neo4j:7687") `
        -u ($env:NEO4J_USER -or "neo4j") `
        -p $env:NEO4J_PASSWORD `
        "CALL apoc.export.json.all('$neo4jFile', {useTypes: true})" 2>$null

    if ($LASTEXITCODE -eq 0 -and (Test-Path $neo4jFile)) {
        $size = [math]::Round((Get-Item $neo4jFile).Length / 1MB, 2)
        Write-Log "Neo4j backup completed: ${size}MB (APOC export)" "SUCCESS"
        $backupFiles += $neo4jFile
    } else {
        # Fallback: use neo4j-admin dump if available
        $neo4jDump = & neo4j-admin dump --database=neo4j --to="$neo4jFile" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Neo4j backup completed (neo4j-admin dump)" "SUCCESS"
            $backupFiles += $neo4jFile
        } else {
            Write-Log "Neo4j backup skipped — neither APOC nor neo4j-admin available" "WARN"
        }
    }
} catch {
    Write-Log "Neo4j backup FAILED: $_" "ERROR"
}

# ───────────────────────────────────────
# Redis Backup (SAVE + copy)
# ───────────────────────────────────────
try {
    Write-Log "Starting Redis backup..."
    $redisDump = "/data/dump.rdb"

    if ($env:REDIS_PASSWORD) {
        & redis-cli -a $env:REDIS_PASSWORD SAVE | Out-Null
    } else {
        & redis-cli SAVE | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        $redisFile = "$BackupDir/redis-$date-$timestamp.rdb"
        if (Test-Path $redisDump) {
            Copy-Item -LiteralPath $redisDump -Destination $redisFile
            $size = [math]::Round((Get-Item $redisFile).Length / 1MB, 2)
            Write-Log "Redis backup completed: ${size}MB" "SUCCESS"
            $backupFiles += $redisFile
        }
    } else {
        throw "Redis SAVE failed"
    }
} catch {
    Write-Log "Redis backup FAILED: $_" "ERROR"
}

# ───────────────────────────────────────
# Upload to S3
# ───────────────────────────────────────
if ($Upload -and $backupFiles.Count -gt 0) {
    Write-Log "Uploading backups to S3..."
    try {
        $s3Path = "s3://$S3Bucket/salesos-backups/$date/"
        foreach ($file in $backupFiles) {
            $fileName = Split-Path $file -Leaf
            Write-Log "Uploading $fileName to $s3Path..."
            if (Get-Command "aws" -ErrorAction SilentlyContinue) {
                & aws s3 cp $file "$s3Path" --endpoint-url $S3Endpoint
            } elseif (Get-Command "azcopy" -ErrorAction SilentlyContinue) {
                & azcopy copy $file "$s3Path$fileName"
            } else {
                Write-Log "No upload tool (aws/azcopy) found — skipping upload" "WARN"
                break
            }
        }
        Write-Log "S3 upload completed" "SUCCESS"
    } catch {
        Write-Log "S3 upload FAILED: $_" "ERROR"
    }
}

# ───────────────────────────────────────
# Retention: clean old backups
# ───────────────────────────────────────
try {
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    $oldFiles = Get-ChildItem -LiteralPath $BackupDir -Filter "*.gz" -File |
        Where-Object { $_.CreationTime -lt $cutoff }

    if ($oldFiles) {
        Write-Log "Removing $($oldFiles.Count) old backup files..."
        foreach ($file in $oldFiles) {
            Remove-Item -LiteralPath $file.FullName -Force
            Write-Log "  Deleted: $($file.Name)"
        }
    } else {
        Write-Log "No old backups to clean"
    }
} catch {
    Write-Log "Retention cleanup FAILED: $_" "WARN"
}

# ───────────────────────────────────────
# Summary
# ───────────────────────────────────────
$status = if ($success) { "SUCCESS" } else { "PARTIAL_FAILURE" }
$summary = @"
SalesOS Backup Summary
══════════════════════
Status:   $status
Date:     $timestamp
Files:    $($backupFiles.Count)
Location: $BackupDir
Size:     $(if($backupFiles.Count -gt 0) { $backupFiles | ForEach-Object { [math]::Round((Get-Item $_).Length / 1MB, 2) + 'MB' } | Join-String -Separator ', ' } else { 'N/A' })
"@
Write-Log $summary
Send-Notification -Status $status -Details $summary

if (-not $success) { exit 1 }
