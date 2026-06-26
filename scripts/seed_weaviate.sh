#!/usr/bin/env bash
# Seed the running Weaviate container via the api container (idempotent).
set -euo pipefail

WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
echo "seed_weaviate.sh: seeding via api container (host view: ${WEAVIATE_URL})..."

docker compose exec -T api python api/seed_weaviate.py

echo "seed_weaviate.sh: vector index seeded (idempotent skip-if-exists)."
