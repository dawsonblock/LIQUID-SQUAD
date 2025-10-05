# LIQUID HIVE 25 — Multi‑Tier LLM + Self‑Loop + Hybrid RAG

[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production‑ready research platform for **iterative reasoning, hybrid RAG, and multi‑tier model execution**. Built with FastAPI, Next.js, Qdrant, Elasticsearch, Postgres, and vLLM. 

Designed for **small, smart models** with tiered escalation to larger backends, self‑loop reasoning (plan → draft → critic → revise), and verifiers for code, math, and retrieval.

---

## 🚀 Features

- **Frontend**: Next.js + Tailwind with API binding
- **API**: FastAPI with health, readiness, and `/ask` endpoint
- **Self‑Loop**: Iterative controller for question answering with critic + verifier integration
- **Model Tiering**: Failover and scaling across local vLLM or remote HTTP endpoints
- **Retrieval**: Dual index (Qdrant vectors + Elasticsearch BM25)
- **Verifiers**: Code execution sandbox, CAS math checker, retrieval provenance enforcer
- **Ops Security**: Auth tokens, rate limiting, observability hooks

---

## 🧩 System Architecture

```
+----------------+          +-------------------+
|   Frontend     |  HTTP    |      API (FastAPI)|
|  (Next.js)     +--------->|   /ask, /healthz  |
+----------------+          +-------------------+
                                   |
                     +-------------+-------------+
                     |                           |
             +-------v------+             +------v-------+
             |  Self-Loop   |             |   Verifiers  |
             | plan→draft→  |             | code|math|RAG |
             | critic→revise|             +--------------+
             +-------+------+
                     |
           +---------v-----------+
           |   ChatClient Tier   |
           | vLLM, remote APIs   |
           +---------+-----------+
                     |
        +------------v------------+
        | Hybrid Retrieval Engine |
        | Qdrant + Elasticsearch  |
        +-------------------------+
```

---

## 📦 Quickstart (Docker)

Requirements: Docker, docker‑compose, Hugging Face token if you use gated models.

```bash
git clone <this-repo>
cd LIQUID_HIVE_25
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

Services:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **Qdrant**: http://localhost:6333
- **Elasticsearch**: http://localhost:9200
- **vLLM**: http://localhost:8001/v1

---

## ⚙️ Environment Variables

| Variable            | Purpose |
|---------------------|---------|
| `HF_TOKEN`          | Hugging Face token |
| `DEV_MODEL`         | Default vLLM model |
| `NEXT_PUBLIC_API_URL` | API URL for frontend |
| `AUTH_TOKENS`       | API tokens for `/ask` |

---

## 📡 API Usage

### `POST /ask`
```json
{"question": "How do I add a reranker?"}
```

### Health
- `GET /healthz` → `{"ok": true}`
- `GET /readyz` → `{"ready": true}`

---

## 🛠 Development Workflow

1. Implement ChatClient tier logic
2. Extend self‑loop criteria
3. Build Qdrant + ES indices
4. Add verifier tests
5. Run CI and deploy

---

## 🧪 Testing

```bash
pytest -q
pytest tests/test_self_loop.py -q
```

---

## 🔒 Security & Ops

- Auth tokens + rate limit (`ops_security/`)
- CORS config via `create_app()`
- Observability counters (`ops_security/observability.py`)
- Recommend TLS proxy + persistent volumes

---

## 🔬 Deep Architecture Notes

- **Self‑Loop**: Implements SPEC‑style loop. Each cycle = Plan → Draft → Critic → Revise. Stops on τ threshold or max rounds.  
- **ChatClient**: Circuit‑breaker, retries, model tiering. Local vLLM used for low‑latency, escalates to stronger remote API when confidence < τ.  
- **Retrieval**: Dual pipeline. ES provides BM25 keyword recall, Qdrant provides dense vector recall. A reranker (roadmap) selects final context.  
- **Verifiers**:  
  - Code: Runs snippets in resource‑limited sandbox.  
  - Math: Symbolic + numeric CAS checker.  
  - Retrieval: Blocks unverifiable claims.  
- **Ops Layer**: Thin wrappers for token‑based auth, rate limiting, and Prometheus‑style metrics.  
- **Data Flow**: User question → API → Self‑loop cycles → Model queries → Retrieval injection → Verifier validation → Final Answer.

---

## 🛣 Roadmap

- Cross‑encoder reranker integration
- Better chunking (hierarchical, ID‑linked)
- Async tool sandbox with quotas
- Continuous eval + regression dashboards
- Helm chart for production deploys

---

## 📂 Repository Layout

```
LIQUID_HIVE_25/
  frontend/                     # Next.js
  full_build_hive_deepseek/
    full_build_upgraded/
      full_build/
        service/                # FastAPI app
        self_loop.py
        chat_client.py
        retrieval/
        verifiers/
        ops_security/
  Dockerfile.api
  Dockerfile.frontend
  docker-compose.dev.yml
  OPERATIONS.md
  DEPLOYMENT.md
```

---

## 🤝 Contributing

PRs welcome. Please:
1. Run `pytest`
2. Add docstrings + type hints
3. Update README/DEPLOYMENT notes

---

## 📜 License

MIT

---

_Generated 2025-10-01T20:11:19.278052Z to reflect the uploaded project's architecture and services._

