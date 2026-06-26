# Integration 10 — Dockerize the Four-Service Stack

Compose the FastAPI backend and Next.js frontend with containerized
Neo4j and Weaviate into a one-command stack. `docker compose up -d --build`
brings the stack to a healthy state; the seed scripts populate the recipe
graph and the vector index; the `/rag` page serves a grounded, cited
answer end-to-end through the browser.

See [TEAM.md](./TEAM.md) for role assignments and
[CONTRIBUTING.md](./CONTRIBUTING.md) for the internal-PR convention.

## Services

| Service    | Image                               | Host port  | Role                              |
| ---------- | ----------------------------------- | ---------- | --------------------------------- |
| `neo4j`    | `neo4j:5-community`                 | 7687, 7474 | Recipe knowledge graph            |
| `weaviate` | `semitechnologies/weaviate:1.24.10` | 8080       | Vector index (external embeddings)|
| `api`      | built from `api/Dockerfile`         | 8000       | FastAPI: `/extract` `/kg` `/rag`  |
| `web`      | built from `web/Dockerfile`         | 3000       | Next.js demo UI                   |

## Runbook — clone to browser demo

```bash
# 1. Clone and enter the repo.
git clone https://github.com/<team-fork-owner>/m10-i10-team-1.git
cd m10-i10-team-1

# 2. Create your .env and set a Neo4j password.
cp .env.example .env
#    Edit .env: set NEO4J_PASSWORD (and keep NEO4J_AUTH=neo4j/<that password>).
#    .env is .gitignore'd — never commit it.

# 3. Build and start all four services.
docker compose up -d --build

# 4. Wait for every service to report healthy.
bash scripts/healthcheck_stack.sh
#    or watch manually:
docker compose ps

# 5. Seed the recipe graph and the vector index (stack must be up).
bash scripts/seed_neo4j.sh
bash scripts/seed_weaviate.sh

# 6. Verify the RAG endpoint returns a grounded, cited answer.
curl -s -X POST http://localhost:8000/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I prep ginger for stir-fry?"}'

# 7. Open the UI and submit the seeded question.
#    http://localhost:3000/rag

# 8. Teardown (drops the named volumes for a clean slate).
docker compose down -v
```

## Host vs. container addressing

| From                        | Neo4j               | Weaviate               | API                     |
| --------------------------- | ------------------- | ---------------------- | ----------------------- |
| api container (Compose DNS) | `bolt://neo4j:7687` | `http://weaviate:8080` | —                       |
| your browser / host         | `localhost:7687`    | `localhost:8080`       | `http://localhost:8000` |

`NEXT_PUBLIC_API_URL` is a **build arg** on `web` (`http://localhost:8000`),
baked into the client bundle at build time — the browser runs on the host
and cannot resolve the Compose service name `api`.

## Troubleshooting

- `ModuleNotFoundError: No module named 'api'` → the api `build.context`
  must be the repo root (`context: .` + `dockerfile: api/Dockerfile`).
- Neo4j never healthy → set `NEO4J_PASSWORD` in `.env`.
- Weaviate inserts vanish → `DEFAULT_VECTORIZER_MODULE` must be `none`.
- api stuck "starting" for minutes → expected on first boot while the
  HuggingFace cache downloads spaCy + flan-t5-base; `start_period` is 180s.
- Seed script `no configuration file provided: not found` → run scripts
  from the repo root, not from inside `scripts/`.
