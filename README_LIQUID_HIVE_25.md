# LIQUID HIVE 25 — Multi‑Tier LLM + Self‑Loop + Hybrid RAG

Production‑ready research stack: FastAPI API, Next.js frontend, iterative self‑loop reasoning, hybrid RAG (Qdrant + Elasticsearch), and a vLLM model server. Designed for small smart models with escalation to larger backends.

## System Overview

```
frontend (Next.js)  →  api (FastAPI)  →  self_loop (plan→draft→critic→revise)
                                      ↘ verifiers (code|math|retrieval)
stores: Postgres (state), Qdrant (vectors), Elasticsearch (BM25), logs
models: vLLM localhost or remote HTTP (tiered)
```

### Core Modules
- **API**: `full_build/service/api.py` — `/healthz`, `/readyz`, `/ask`
- **Self‑Loop**: `full_build/self_loop.py` — plan→draft→critic→revise with stop criteria
- **Model Tiering**: `full_build/chat_client.py` — retries, timeouts, circuit‑breaker
- **Retrieval**: `full_build/retrieval/*` — dual index, crawler, utils, Qdrant + ES
- **Verifiers**: `full_build/verifiers/*` — unit‑test runner, CAS math checks, citation provenance
- **Ops**: `full_build/ops_security/*` — auth, rate‑limit, basic observability

## Quickstart (Dev, Docker)

Requirements: Docker, docker‑compose, a Hugging Face token if you pull gated models.

```bash
git clone <this-repo>
cd LIQUID_HIVE_25
cp .env.example .env  # then edit values
docker compose -f docker-compose.dev.yml up --build
```

Services exposed:
- Frontend: http://localhost:3000
- API: http://localhost:8000  (`/healthz`, `/readyz`, `/ask`)
- Qdrant: http://localhost:6333
- Elasticsearch: http://localhost:9200
- vLLM (OpenAI‑compatible): http://localhost:8001/v1

### Key Environment Variables
- `HF_TOKEN` — Hugging Face token (optional, for gated models)
- `DEV_MODEL` — default vLLM model (default `microsoft/DialoGPT-small`)
- `NEXT_PUBLIC_API_URL` — frontend → API base URL (defaults to `http://localhost:8000` in compose)
- `AUTH_TOKENS` — comma‑separated API tokens for `/ask` (set in a `.env` then wired in bootstrap if desired)

## API

### `POST /ask`
Request:
```json
{"question": "How do I add a cross‑encoder reranker?"}
```
Headers:
```
Authorization: <token>   # if Authenticator is configured with non‑empty tokens
```

Response:
```json
{"answer": "<final self‑loop answer>" }
```

Health:
- `GET /healthz` → `{"ok": true}`
- `GET /readyz` → `{"ready": true}`

## Frontend

Directory: `frontend/` (Next.js + React + Tailwind). Configure `NEXT_PUBLIC_API_URL`. Run via compose or locally:

```bash
cd frontend
npm i
npm run dev
```

## Running the API without Docker

```bash
python -m uvicorn full_build.service.api:app --host 0.0.0.0 --port 8000 --reload
```

To attach the self‑loop and auth/rate‑limit, use `full_build/service/bootstrap.py` or create an entrypoint that imports `create_app()` and injects dependencies.

## Data Engines

- **Postgres**: conversation state or audit trails. Migrate/seed as needed.
- **Qdrant**: vector store for embeddings. Collection naming lives in `retrieval/*`.
- **Elasticsearch**: BM25 inverted index for hybrid search. Single‑node dev config in compose.
- **Crawler**: snapshot HTML → text for reproducible RAG.

## Development Flow

1. Implement or point `ChatClient` to your model(s) (local vLLM or remote).
2. Tune self‑loop stop criteria and verifier thresholds.
3. Build hybrid index with `retrieval/dual_index.py` and your corpus.
4. Add unit tests for verifiers and the self‑loop controller.
5. Run CI, ship container images, promote to staging.

## Testing

Add or run tests under `tests/` if present. Example patterns:
```bash
pytest -q
pytest tests/test_self_loop.py -q
```

## Security & Ops

- **Auth**: `ops_security/security.py` token allow‑list.
- **Rate limiting**: per‑user + per‑endpoint in `RateLimiter`.
- **Observability**: request duration and error counters in `ops_security/observability.py`.
- **CORS**: set `allowed_origins` in `create_app()`.

Hardening checklist:
- Enforce HTTPS behind a reverse proxy (Caddy, Nginx, Traefik).
- Persist Postgres and Qdrant volumes.
- Configure ES auth in non‑dev.
- Resource caps for vLLM and API pods.

## Roadmap

- Cross‑encoder reranker (e.g., `bge‑reranker‑base`) post‑retrieval.
- Better chunking with section headers and IDs.
- Async tool sandbox with resource limits for code execution.
- Continuous evaluation harness and regression plots.
- Production Helm chart with values for model tiers.

## Repository Map

```
LIQUID_HIVE_25/
  frontend/                     # Next.js UI
  full_build_hive_deepseek/
    full_build_upgraded/
      full_build/
        service/                # FastAPI app + bootstrap
        self_loop.py
        chat_client.py
        retrieval/              # Qdrant + ES
        verifiers/              # code|math|retrieval verifiers
        ops_security/           # auth, rate‑limit, observability
  Dockerfile.api
  Dockerfile.frontend
  docker-compose.dev.yml
  OPERATIONS.md
  DEPLOYMENT.md
```

## License

MIT. See `LICENSE`.

---

_This README was generated 2025-10-01T20:02:33.761135Z from the uploaded LIQUID HIVE project bundle to match the actual directory layout and services in `docker-compose.dev.yml`._
