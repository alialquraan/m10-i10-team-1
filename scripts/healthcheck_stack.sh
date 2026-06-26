#!/usr/bin/env bash
# Poll until all four services report healthy, or until the budget expires.
set -euo pipefail

SERVICES=(neo4j weaviate api web)
MAX_ITERS=45
SLEEP_SECS=2

status_of() {
  local svc="$1" cid
  cid="$(docker compose ps -q "$svc" 2>/dev/null || true)"
  if [[ -z "$cid" ]]; then
    echo "missing"
    return
  fi
  docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cid" 2>/dev/null || echo "missing"
}

for ((i = 1; i <= MAX_ITERS; i++)); do
  all_healthy=true
  line=""
  for svc in "${SERVICES[@]}"; do
    s="$(status_of "$svc")"
    line+="$svc=$s "
    [[ "$s" == "healthy" ]] || all_healthy=false
  done
  echo "[$i/$MAX_ITERS] $line"
  if $all_healthy; then
    echo "healthcheck_stack.sh: all four services healthy."
    exit 0
  fi
  sleep "$SLEEP_SECS"
done

echo "healthcheck_stack.sh: timed out waiting for all services to be healthy." >&2
echo "  Inspect with: docker compose ps   and   docker compose logs <service>" >&2
exit 1
