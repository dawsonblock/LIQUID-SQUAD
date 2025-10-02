# LIQUID HIVE 25 Architecture

## High‑Level

```
Frontend (Next.js) → API (FastAPI) → Self‑Loop
                                       ↘ Verifiers
Stores: Postgres, Qdrant, Elasticsearch
Models: vLLM / Remote API tiered
```

## Components

### Frontend
- Next.js + Tailwind
- Configured with `NEXT_PUBLIC_API_URL`

### API
- FastAPI app in `full_build/service/api.py`
- Endpoints: `/ask`, `/healthz`, `/readyz`
- Bootstrapped via `bootstrap.py`

### Self‑Loop
- File: `self_loop.py`
- Implements iterative reasoning cycle:
  - Plan → Draft → Critic → Revise
  - Stops on τ or max rounds
- Hooks into verifiers and ChatClient

### ChatClient (Model Tiering)
- File: `chat_client.py`
- Handles retries, timeouts, and model escalation
- Local vLLM for latency, remote APIs for quality

### Retrieval Engine
- Directory: `retrieval/`
- Qdrant: dense vector search
- Elasticsearch: BM25 keyword recall
- Supports hybrid retrieval + reranking

### Verifiers
- Directory: `verifiers/`
- **CodeVerifier**: sandboxed execution
- **MathVerifier**: symbolic + numeric checks
- **RetrievalVerifier**: citation enforcement

### Ops & Security
- Directory: `ops_security/`
- Authenticator: token allow‑list
- RateLimiter: per‑user + endpoint
- Observability: request/error metrics

## Data Flow

```
User → Frontend → API → Self‑Loop
         → Retrieval (Qdrant+ES)
         → Model (ChatClient tiered)
         → Verifiers
         → Final Answer
```

## Deployment

- Dev: `docker-compose.dev.yml`
- Services: API, Frontend, Postgres, Qdrant, Elasticsearch, vLLM
- Production: use Helm/overlays with TLS and persistent volumes

---

_Generated 2025-10-01T20:16:54.951111Z_
