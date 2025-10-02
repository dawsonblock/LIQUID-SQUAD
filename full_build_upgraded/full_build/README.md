# LIQUID-SQUAD: Production-Grade AI Agent System

This build provides a scalable foundation for a self-improving question answering agent built from language models.  It implements a **dual-index retrieval system**, a **self-loop controller** with verifiers, domain routing, evaluation harness and a simple memory/cache layer.  Each component is cleanly separated so you can swap in your own models, datasets or storage back-ends.

## Features

- **Dual-Index RAG** – combines a dense embedding index with a sparse BM25 index.  At query time the two scores are cross-scored to return a ranked list of documents and associated citations.
- **Self-Loop Controller** – runs iterative cycles of plan → draft → critic → verify → revise until a confidence threshold is met.  Integrates external verifiers for code and math, and includes citation checking for retrieved facts.
- **Verifiers** – syntax and static analysis for code blocks, symbolic checking for math expressions, and citation/consistency checks for retrieved facts.
- **Tiered Model Client** – HTTP-based model client with automatic tier escalation, circuit breakers, and retry logic for OpenAI/vLLM-compatible endpoints.
- **Evaluation Harness** – allows you to run regression tests and compute metrics such as exact match, F1, pass@1 and citation precision.
- **Memory and Cache** – simple long-term store with pruning and a key-value cache for plans and answers.
- **Ops/Security** – authentication via Bearer tokens, rate limiting, Prometheus metrics, and structured logging.

## Quick Start

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000

# Authentication (optional - if not set, no auth required)
AUTH_TOKEN=your-secret-token-here

# Rate limiting
RATE_LIMIT_QPS=5
RATE_LIMIT_WINDOW=60

# CORS
CORS_ORIGINS=*

# Model configuration
PRIMARY_MODEL_URL=http:
BACKUP_MODEL_URL=http:
MODEL_API_KEY=your-api-key
MODEL_NAME=gpt-3.5-turbo

# Retrieval configuration
RETRIEVAL_MODE=disabled  # Options: disabled, dense, sparse, dual
QDRANT_URL=http:
ES_URL=http:
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Self-loop configuration
MAX_ROUNDS=3
CONFIDENCE_THRESHOLD=0.65

# Code execution (off by default for security)
CODE_EXEC=off
```

### Running Locally

1.  Install dependencies:

    ```bash
    cd full_build_upgraded/full_build
    pip install -r requirements.txt
    ```

2.  Set environment variables (or create `.env` file)

3.  Run the API server:

    ```bash
    # Option 1: Using uvicorn directly
    uvicorn full_build.service.api:app --host 0.0.0.0 --port 8000
    
    # Option 2: Using bootstrap script
    python -m full_build.service.bootstrap
    ```

4.  Test the API:

    ```bash
    # Health check
    curl http:
    
    # Ask a question (no auth)
    curl -X POST http:
     -H "Content-Type: application/json" \
     -d '{"question": "What is 2+2?"}'
    
    # Ask a question (with auth)
    curl -X POST http:
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-secret-token-here" \
     -d '{"question": "What is 2+2?"}'
    ```

### Running with Docker

1.  Build the image:

    ```bash
    cd full_build_upgraded/full_build
    docker build -t liquid-squad:latest .
    ```

2.  Run the container:

    ```bash
    docker run -p 8000:8000 \
     -e PRIMARY_MODEL_URL=http:
     -e RETRIEVAL_MODE=disabled \
     liquid-squad:latest
    ```

### Running with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: ./full_build_upgraded/full_build
    ports:
      - "8000:8000"
    environment:
      - PRIMARY_MODEL_URL=http:
      - RETRIEVAL_MODE=disabled
      - AUTH_TOKEN=your-secret-token
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http:
      interval: 30s
      timeout: 3s
      retries: 3
```

Run with:

```bash
docker-compose up
```

## API Specification

### Endpoints

#### `GET /health`

Liveness probe. Always returns 200 if the service is running.

**Response:**

```json
{"ok": true}
```

#### `GET /ready`

Readiness probe. Checks downstream services (Qdrant/ES) if retrieval is enabled.

**Response:**

```json
{"ready": true}
```

#### `GET /metrics`

Prometheus metrics endpoint. Returns metrics in Prometheus text format.

#### `POST /ask`

Main question-answering endpoint.

**Request:**

```json
{
  "question": "What is the capital of France?"
}
```

**Headers:**

- `Authorization: Bearer <token>` (required if `AUTH_TOKEN` is set)
- `Content-Type: application/json`

**Response:**

```json
{
  "answer": "The capital of France is Paris.",
  "citations": ["doc_1", "doc_2"]
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid or missing auth token
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Processing error

## Testing

Run tests with pytest:

```bash
cd full_build_upgraded/full_build
pytest tests/ -v
```

Run specific test files:

```bash
pytest tests/test_health.py -v
pytest tests/test_auth.py -v
pytest tests/test_ask_disabled_retrieval.py -v
```

## Configuration Modes

### Retrieval Disabled (Simplest)

```bash
RETRIEVAL_MODE=disabled
PRIMARY_MODEL_URL=http:
```

This mode runs the self-loop without retrieval. Suitable for general Q&A without external knowledge.

### Retrieval Enabled

```bash
RETRIEVAL_MODE=dual  # or dense, sparse
QDRANT_URL=http:
ES_URL=http:
PRIMARY_MODEL_URL=http:
```

This mode enables RAG with Qdrant (dense) and Elasticsearch (sparse) backends.

## Architecture

```
full_build/
├── README.md              # this file
├── Dockerfile             # production Docker image
├── requirements.txt       # Python dependencies
├── config/                # configuration files
│   └── settings.py        # environment-based settings
├── service/               # API layer
│   ├── api.py            # FastAPI application
│   └── bootstrap.py      # application factory
├── chat_client.py         # HTTP model client with tiering
├── self_loop.py           # core self-loop controller
├── retrieval/             # dual-index RAG and utilities
├── verifiers/             # code/math/retrieval verifiers
├── ops_security/          # auth, rate limiting, metrics
└── tests/                 # pytest test suite
```

## Production Considerations

1.  **Authentication**: Always set `AUTH_TOKEN` in production
2.  **Rate Limiting**: Adjust `RATE_LIMIT_QPS` based on your capacity
3.  **Model Endpoints**: Use production-grade model endpoints with proper timeouts
4.  **Retrieval**: Start with `RETRIEVAL_MODE=disabled` and enable when needed
5.  **Monitoring**: Use `/metrics` endpoint with Prometheus/Grafana
6.  **Health Checks**: Configure k8s/Docker health checks using `/health` and `/ready`
7.  **Code Execution**: Keep `CODE_EXEC=off` unless you have proper sandboxing

## License

See LICENSE file for details.
