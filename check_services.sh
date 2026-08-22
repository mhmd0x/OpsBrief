#!/usr/bin/env bash
set -euo pipefail

source /root/OpsBrief/.env.monitoring

cd /root/OpsBrief

api_health="$(docker inspect -f '{{.State.Health.Status}}' opsbrief-api-1)"
db_health="$(docker inspect -f '{{.State.Health.Status}}' opsbrief-database-1)"
caddy_state="$(systemctl is-active caddy)"

if [[ "$api_health" != "healthy" ]]; then
    exit 1
fi

if [[ "$db_health" != "healthy" ]]; then
    exit 1
fi

if [[ "$caddy_state" != "active" ]]; then
    exit 1
fi

curl -fsS "$OPSBRIEF_SERVICES_PUSH_URL" >/dev/null
