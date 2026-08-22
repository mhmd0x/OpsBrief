#!/usr/bin/env bash
set -euo pipefail

source "/root/OpsBrief/.env.monitoring"

BACKUP_DIR="/root/OpsBrief/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/opsbrief_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

cd "/root/OpsBrief"

docker compose exec -T database \
  pg_dump -U opsbrief -d opsbrief \
  > "$BACKUP_FILE"

find "$BACKUP_DIR" -type f -name 'opsbrief_*.sql' -mtime +7 -delete
curl -fsS --retry 3 "$OPSBRIEF_BACKUP_PUSH_URL" >/dev/null
