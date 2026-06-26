cat > TEAM.md << 'EOF'
# Team Roster — Module 10 Integration

This file is the team roster artifact for the Module 10 four-service Docker Compose Integration. The instructional team assigns roles; the team fills in identifier, branch, and Slack fields.

> No personal names in this file. Identifiers below are GitHub usernames, which match `git log --author` for TA attribution.

> Composition note: this is a 2-Team-Member team. Per the fallback below, the Frontend lead and Infra-Integration lead roles are merged into a single Team Member. Confirm the 2-member composition with your TA — the roster is instructional-team-assigned.

---

## Team Identity

- Team name: TODO_team_name
- Team Slack channel: TODO_slack_channel
- Team-formation date: TODO_yyyy_mm_dd
- Designated team submitter: alialquraan (Backend lead — owns the team fork)

---

## Team Roster

| Role | GitHub username | Assigned by | Branch | Internal-PR reviewer | Primary files owned |
|---|---|---|---|---|---|
| Backend lead | alialquraan | Instructional team | `backend/api-endpoints` | Frontend lead + Infra-Integration lead | `api/main.py`, `api/models.py`, `api/rag.py`, `api/deps.py`, `api/Dockerfile` |
| Frontend lead + Infra-Integration lead (merged) | YOUR_GH_USERNAME | Instructional team | `frontend/nextjs-pages` + `infra/docker-compose` | Backend lead | `web/pages/{extract,kg,rag}.tsx`, `web/lib/types.ts`, `web/Dockerfile`, `tests/frontend/playwright/*`, `docker-compose.yml`, `scripts/seed_neo4j.sh`, `scripts/seed_weaviate.sh`, `scripts/healthcheck_stack.sh`, `.env.example`, `README.md` |

> The merged Team Member keeps both branch names (`frontend/nextjs-pages` and `infra/docker-compose`) because the autograder and TA cross-reference scripts look for those exact names. Frontend work lands on `frontend/nextjs-pages`; infra work lands on `infra/docker-compose`. Each opens its own internal PR against `main`.

Fallback compositions for non-3-Team-Member teams:

- 2 Team Members: Frontend and Infra-Integration roles merge. The merged Team Member owns all `web/`, `docker-compose.yml`, and `seed_*.sh` files. (This team's composition.)
- 4 Team Members: Infra-Integration splits into "Compose + healthchecks" and "Seed + runbook". The two Team Members internal-review each other.

---

## Per-Role File Checklist (TA grading cross-reference)

### Backend lead — alialquraan

- [ ] `api/main.py` — path operations, lifespan, CORS middleware
- [ ] `api/models.py` — Pydantic shapes
- [ ] `api/rag.py` — RAG composer with grounding contract
- [ ] `api/deps.py` — Depends() functions
- [ ] `api/Dockerfile` — single-stage Python

### Frontend lead + Infra-Integration lead — YOUR_GH_USERNAME

Frontend surface:

- [ ] `web/pages/extract.tsx` (shipped pre-implemented; owned, not authored)
- [ ] `web/pages/kg.tsx` (shipped pre-implemented; owned, not authored)
- [ ] `web/pages/rag.tsx` (shipped pre-implemented; owned, not authored)
- [ ] `web/lib/types.ts` (shipped pre-implemented; mirrors Pydantic field-for-field)
- [ ] `web/Dockerfile` (shipped pre-implemented; intentional node:20-slim)
- [x] `tests/frontend/playwright/*.spec.ts` (authored — one smoke test per page)

Infra-Integration surface:

- [x] `docker-compose.yml` — four services, healthchecks, depends_on chain, named volumes
- [x] `scripts/seed_neo4j.sh`
- [x] `scripts/seed_weaviate.sh`
- [x] `scripts/healthcheck_stack.sh`
- [ ] `.env.example` (shipped pre-implemented; no real credentials)
- [x] `README.md` runbook
- [ ] `tests/integration/test_stack_e2e.py` (optional scaffold — autograder does not run it)

---

## Escalation Checklist (apply in order)

1. Inline comment on the internal PR — state the disagreement and link the contract artifact.
2. Team Slack channel with the TA tagged — allow up to 4 working hours.
3. Support Instructor — if the TA decision is contested or the TA is unavailable.
4. Lead Instructor — only if a role-rebalancing decision is needed.

Document the escalation path taken in the team submission PR description.

---

## Contract-Change Protocol

- Backend lead announces any Pydantic shape change on the team Slack channel before the change lands.
- Frontend lead + Infra-Integration lead requests new backend fields via an internal-PR comment on the Backend lead's branch — does not assume — and announces any `.env` or DNS-affecting change before it lands.

The protocol is enforced by the internal-PR review — the reviewer rejects PRs where the contract change was not announced.

---

## Submission

When both role branches merge to the team fork's `main` and `docker compose up -d` smoke passes locally for each Team Member:

1. The team submitter pastes the team fork URL into TalentLMS → Module 10 → Integration Task.
2. Each Team Member separately submits the participation-confirmation TalentLMS unit naming their assigned role and the files they authored.

Two-tier grading: team tier 60 pts + per-role tier 40 pts.
EOF