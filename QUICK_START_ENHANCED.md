# Quick Start Guide - Enhanced LIQUID HIVE 25

This guide will help you quickly get started with the enhanced LIQUID HIVE 25 system.

---

## 🚀 Quick Start (5 Minutes)

### 1. Basic Setup

```bash
cd /workspace/full_build_upgraded/full_build

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Set Essential Environment Variables

```bash
export RETRIEVAL_MODE=disabled
export AUTH_TOKEN=dev-token-12345
export LOG_LEVEL=INFO
```

### 3. Start the Server

#### Option A: Use the Original API
```bash
python -m full_build.service.bootstrap
```

#### Option B: Use the Enhanced API (Recommended)
```bash
uvicorn full_build.service.api_enhanced:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test It

```bash
# Health check
curl http://localhost:8000/health

# Make a query
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Python?",
    "use_cache": true
  }'
```

---

## 🎯 Key Features & How to Use Them

### 1. Response Caching

**Save API costs and get instant responses for repeated questions:**

```bash
# First request (slow - executes self-loop)
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?", "use_cache": true}'

# Second request (fast - from cache)
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?", "use_cache": true}'

# Check cache stats
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:8000/stats
```

---

### 2. Conversation Management

**Have multi-turn conversations with context:**

```bash
# Start a conversation
RESPONSE=$(curl -s -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?"}')

# Extract conversation_id
CONV_ID=$(echo $RESPONSE | jq -r '.conversation_id')

# Continue the conversation
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"What are its main features?\",
    \"conversation_id\": \"$CONV_ID\"
  }"

# List all conversations
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:8000/conversations

# Get conversation details
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:8000/conversations/$CONV_ID
```

---

### 3. Export Results

**Export responses in different formats:**

```bash
# Export as Markdown
curl -X POST "http://localhost:8000/ask/export?format=markdown" \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain quantum computing"}' \
  -o result.md

# Export as HTML
curl -X POST "http://localhost:8000/ask/export?format=html" \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain quantum computing"}' \
  -o result.html

# Export as JSON
curl -X POST "http://localhost:8000/ask/export?format=json" \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain quantum computing"}' \
  -o result.json
```

---

### 4. Real-Time Streaming

**Get real-time updates as the system thinks:**

```bash
curl -X POST http://localhost:8000/ask/stream \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain neural networks"}' \
  --no-buffer
```

**Output:**
```
data: {"type":"iteration","data":{"step":"plan",...}}
data: {"type":"iteration","data":{"step":"draft",...}}
data: {"type":"iteration","data":{"step":"verify",...}}
data: {"type":"iteration","data":{"step":"critic",...}}
data: {"type":"iteration","data":{"step":"revise",...}}
data: {"type":"final","data":{"answer":"...",...}}
```

---

### 5. Monitoring & Metrics

**Access Prometheus metrics:**

```bash
# View all metrics
curl http://localhost:8000/metrics

# Filter specific metrics
curl http://localhost:8000/metrics | grep cache

# View stats
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:8000/stats
```

**Key Metrics:**
- `cache_hits_total` / `cache_misses_total` - Cache performance
- `selfloop_duration_ms` - Execution time
- `selfloop_confidence` - Answer quality
- `model_tier_usage_total` - Model distribution
- `request_latency_seconds` - API response time

---

## ⚙️ Configuration

### Essential Environment Variables

```bash
# Model URLs (optional if using external services)
export SMALL_MODEL_URL=http://localhost:8001
export MEDIUM_MODEL_URL=http://localhost:8002
export LARGE_MODEL_URL=http://localhost:8003

# Retrieval (set to "disabled" if not using)
export RETRIEVAL_MODE=disabled
# Or enable with: hybrid, qdrant, elasticsearch
export QDRANT_URL=http://localhost:6333
export ES_URL=http://localhost:9200

# Security
export AUTH_TOKEN=your-secret-token
export CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Cache
export CACHE_MAX_SIZE=100
export CACHE_TTL_SECONDS=3600

# Timeouts (in seconds)
export TIMEOUT_REQUEST=300.0
export TIMEOUT_SELFLOOP=180.0
export TIMEOUT_MODEL=30.0

# Rate Limiting
export RATE_LIMIT_QPS=5
export RATE_LIMIT_WINDOW=60

# Logging
export LOG_LEVEL=INFO
export LOG_STRUCTURED=true
```

---

## 🐳 Docker Compose (Full Stack)

```bash
cd /workspace/hive_deploy

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api

# Stop all services
docker compose down
```

**Services:**
- API: http://localhost:8000
- Frontend: http://localhost:3000
- Qdrant: http://localhost:6333
- Elasticsearch: http://localhost:9200
- vLLM (Small): http://localhost:8001
- vLLM (Medium): http://localhost:8002
- vLLM (Large): http://localhost:8003

---

## 🧪 Testing

### Run Tests

```bash
cd /workspace/full_build_upgraded/full_build

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=full_build --cov-report=html
```

### Test the Cache

```python
from full_build.response_cache import get_cache

cache = get_cache()

# Put something in cache
from full_build.self_loop import SelfLoopResult, IterationRecord
result = SelfLoopResult(
    answer="Test answer",
    citations=[],
    iterations=[],
    model_tier="small",
    retrieval_mode="disabled",
    total_duration_ms=100,
    rounds=1
)

cache.put("test question", result)

# Get it back
cached = cache.get("test question")
print(cached.answer)  # "Test answer"

# Check stats
print(cache.stats())
```

### Test Input Validation

```python
from full_build.input_validation import QuestionValidator

validator = QuestionValidator()

# Valid question
result = validator.validate("What is Python?")
print(result.is_valid)  # True

# Invalid question (too short)
result = validator.validate("Hi")
print(result.is_valid)  # False
print(result.errors)  # List of errors
```

---

## 📊 Monitoring Dashboard

### Grafana Setup (Optional)

```bash
# Create docker-compose-monitoring.yml
cat > docker-compose-monitoring.yml << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
EOF

# Create prometheus.yml
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'liquid-hive'
    static_configs:
      - targets: ['host.docker.internal:8000']
EOF

# Start monitoring stack
docker compose -f docker-compose-monitoring.yml up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## 🔧 Troubleshooting

### Issue: "handler_not_configured" error

**Solution:** Make sure you're using the bootstrap script or properly initializing the API:

```python
# In your startup code
from full_build.service.bootstrap import create_app

app = create_app()
```

### Issue: Cache not working

**Check:**
1. Is `use_cache=true` in your request?
2. Are you using the same parameters?
3. Has the cache expired? (check TTL)

```bash
# Clear cache if needed
curl -X DELETE http://localhost:8000/cache \
  -H "Authorization: Bearer dev-token-12345"
```

### Issue: Timeout errors

**Solution:** Increase timeout values:

```bash
export TIMEOUT_REQUEST=600.0
export TIMEOUT_SELFLOOP=300.0
```

### Issue: Rate limit exceeded

**Solution:** Increase rate limits or wait:

```bash
export RATE_LIMIT_QPS=10
export RATE_LIMIT_WINDOW=60
```

---

## 📚 API Reference

### POST /ask

**Request:**
```json
{
  "question": "string (required, 3-5000 chars)",
  "conversation_id": "string (optional)",
  "use_cache": "boolean (optional, default: true)",
  "max_rounds": "int (optional, 1-10)",
  "conf_threshold": "float (optional, 0.0-1.0)"
}
```

**Response:**
```json
{
  "answer": "string",
  "citations": ["string"],
  "iterations": [{"step": "...", "content": "...", ...}],
  "model_tier": "small|medium|large",
  "retrieval_mode": "disabled|qdrant|elasticsearch|hybrid",
  "duration_ms": 2500,
  "rounds": 2,
  "from_cache": false,
  "conversation_id": "uuid"
}
```

### GET /stats

**Response:**
```json
{
  "cache": {
    "size": 10,
    "max_size": 100,
    "hits": 50,
    "misses": 30,
    "hit_rate": 0.625,
    "total_requests": 80
  },
  "conversations": {
    "total_conversations": 5,
    "total_turns": 20,
    "active_users": 3,
    "max_conversations": 100
  }
}
```

### GET /conversations

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "uuid",
      "user_id": "string",
      "turn_count": 5,
      "created_at": 1234567890.0,
      "updated_at": 1234567890.0,
      "duration_seconds": 300.0
    }
  ],
  "total": 1
}
```

---

## 🎓 Examples

### Python Client Example

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "dev-token-12345"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Simple query
response = requests.post(
    f"{API_URL}/ask",
    json={"question": "What is Python?"},
    headers=headers
)
result = response.json()
print(result["answer"])

# With conversation
response = requests.post(
    f"{API_URL}/ask",
    json={
        "question": "What is Python?",
        "use_cache": True
    },
    headers=headers
)
conv_id = response.json()["conversation_id"]

# Follow-up question
response = requests.post(
    f"{API_URL}/ask",
    json={
        "question": "What are its main uses?",
        "conversation_id": conv_id
    },
    headers=headers
)
print(response.json()["answer"])
```

### JavaScript/TypeScript Client Example

```typescript
const API_URL = "http://localhost:8000";
const TOKEN = "dev-token-12345";

async function askQuestion(question: string) {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question })
  });
  
  return await response.json();
}

// Usage
const result = await askQuestion("What is machine learning?");
console.log(result.answer);
```

---

## 🎉 Next Steps

1. **Explore the API** - Try different queries and features
2. **Check Metrics** - Monitor performance at `/metrics`
3. **Read Full Docs** - See `ENHANCEMENTS_COMPLETE.md`
4. **Configure for Production** - Update environment variables
5. **Set up Monitoring** - Add Grafana dashboards
6. **Scale Up** - Use Docker Compose for full stack

---

## 📞 Need Help?

- **Documentation**: See `ENHANCEMENTS_COMPLETE.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Configuration**: See `config/validation.py` for all options
- **API Details**: See `service/api_enhanced.py`

---

**Happy Hiving! 🐝**
