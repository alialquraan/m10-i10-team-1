#!/usr/bin/env bash
# Seed the running Neo4j container with the recipe fixture (idempotent).
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${NEO4J_USER:?NEO4J_USER not set — copy .env.example to .env and fill it in}"
: "${NEO4J_PASSWORD:?NEO4J_PASSWORD not set — copy .env.example to .env and fill it in}"

docker compose exec -T neo4j \
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
  < api/seed.cypher

echo "seed_neo4j.sh: recipe graph seeded into neo4j (idempotent MERGE)."
