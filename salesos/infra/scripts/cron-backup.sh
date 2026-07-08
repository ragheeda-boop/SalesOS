#!/bin/bash
set -euo pipefail

# Runs backup-db.sh inside the backup container via docker compose.
# Intended to be called from a cron job on the host.
# Example crontab (daily at 2am):
#   0 2 * * * /path/to/salesos/infra/scripts/cron-backup.sh >> /var/log/salesos-backup.log 2>&1

cd "$(dirname "$0")/../.."
docker compose --profile backup run --rm backup backup-db
