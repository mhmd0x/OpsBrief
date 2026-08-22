#!/usr/bin/env bash
set -euo pipefail

source "/root/OpsBrief/.env.monitoring"

THRESHOLD=85
USAGE=$(df / --output=pcent | tail -1 | tr -dc '0-9')

if [ "$USAGE" -ge "$THRESHOLD" ]; then
    exit 1
fi

curl -fsS "$OPSBRIEF_DISK_PUSH_URL" >/dev/null
