# 🔧 LIQUID HIVE 25 - Operations Manual

This document provides comprehensive operational procedures for managing, monitoring, and maintaining the LIQUID HIVE 25 system in production environments.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Self-Loop Reasoning System](#self-loop-reasoning-system)
3. [Deployment Procedures](#deployment-procedures)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Backup & Recovery](#backup--recovery)
6. [Scaling & Performance](#scaling--performance)
7. [Security Operations](#security-operations)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Disaster Recovery](#disaster-recovery)
11. [CI/CD Pipeline](#cicd-pipeline)

## 🏗️ System Overview

### Architecture Components

| Component | Purpose | Technology | Port | Health Check |
|-----------|---------|------------|------|--------------|
| Frontend | User Interface | Next.js 14 | 3000 | `/api/health` |
| API Gateway | Request Routing | Nginx | 80/443 | `/health` |
| API Service | Core Logic | FastAPI | 8000 | `/health` |
| vLLM Tier 1 | Light Models | vLLM | 8001 | `/health` |
| vLLM Tier 2 | Medium Models | vLLM | 8002 | `/health` |
| vLLM Tier 3 | Heavy Models | vLLM | 8003 | `/health` |
| PostgreSQL | Primary Database | PostgreSQL 15 | 5432 | `pg_isready` |
| Qdrant | Vector Database | Qdrant | 6333 | `/health` |
| Elasticsearch | Search Engine | Elasticsearch 8.11 | 9200 | `/_cluster/health` |
| Redis | Cache & Sessions | Redis 7 | 6379 | `ping` |
| Prometheus | Metrics Collection | Prometheus | 9090 | `/-/healthy` |
| Grafana | Monitoring Dashboard | Grafana | 3001 | `/api/health` |

### Resource Requirements

#### Minimum Production Requirements
- **CPU**: 16 cores (32 threads recommended)
- **RAM**: 32GB (64GB recommended)
- **GPU**: NVIDIA GPU with 16GB+ VRAM
- **Storage**: 200GB SSD (500GB recommended)
- **Network**: 1Gbps connection

#### Recommended Production Setup
- **CPU**: 32 cores (Intel Xeon or AMD EPYC)
- **RAM**: 128GB DDR4/DDR5
- **GPU**: NVIDIA A100 40GB or RTX 4090
- **Storage**: 1TB NVMe SSD + 2TB HDD for backups
- **Network**: 10Gbps connection with redundancy

## 🧠 Self-Loop Reasoning System

### Architecture Overview

The Self-Loop is the core reasoning engine that implements an iterative self-improvement process for query responses.

```
┌─────────────────────────────────────────┐
│  1. PLAN                                │
│  - Analyze user query                   │
│  - Break down into sub-problems         │
│  - Identify verification requirements   │
│  - Select appropriate verifiers         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  2. DRAFT                               │
│  - Route to ChatClient (tiered models)  │
│  - Generate initial response            │
│  - Execute code if needed               │
│  - Retrieve additional context          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  3. CRITIC                              │
│  - CodeVerifier: Syntax & execution     │
│  - MathVerifier: Calculation accuracy   │
│  - RetrievalVerifier: Factual grounding │
│  - Calculate confidence score (τ)       │
│  - Generate improvement feedback        │
└──────────────┬──────────────────────────┘
               ↓
         [τ ≥ threshold?]
          Yes ↓    ↓ No
         DONE    ↓
                 ↓
┌─────────────────────────────────────────┐
│  4. REVISE                              │
│  - Incorporate critic feedback          │
│  - Fix identified errors                │
│  - Improve reasoning chain              │
│  - Re-retrieve if context insufficient  │
└──────────────┬──────────────────────────┘
               ↓
        [max_rounds reached?]
          No → back to PLAN (Round n+1)
          Yes → return best attempt
```

### Configuration Parameters

```bash
# .env configuration for Self-Loop
SELF_LOOP_MAX_ROUNDS=5              # Maximum iteration rounds
SELF_LOOP_CONFIDENCE_THRESHOLD=0.85  # Tau (τ) stopping threshold
SELF_LOOP_TIMEOUT_SECONDS=300        # Total execution timeout
SELF_LOOP_ENABLE_CODE_EXEC=true      # Allow code execution
SELF_LOOP_ENABLE_RETRIEVAL=true      # Enable RAG during iterations
SELF_LOOP_ENABLE_MATH_VERIFY=true    # Enable math verification
```

### Monitoring Self-Loop Performance

#### Key Metrics to Track

```bash
# Prometheus metrics
self_loop_rounds_total                    # Total rounds per query
self_loop_confidence_score                # Final confidence (τ) achieved
self_loop_duration_seconds                # Total execution time
self_loop_verifier_failures_total         # Verifier failure count
self_loop_early_stopping_total            # Queries that stopped early (good)
self_loop_max_rounds_reached_total        # Queries hitting max rounds (review)
```

#### Grafana Dashboard Queries

```promql
# Average rounds per query
avg(self_loop_rounds_total)

# Success rate (τ ≥ threshold)
sum(rate(self_loop_confidence_score{score>=0.85}[5m])) / 
sum(rate(self_loop_confidence_score[5m]))

# P95 latency
histogram_quantile(0.95, rate(self_loop_duration_seconds_bucket[5m]))

# Verifier performance
rate(self_loop_verifier_failures_total[5m]) by (verifier_type)
```

#### Health Checks

```bash
# Check Self-Loop system status
curl http://localhost:8000/api/v1/self-loop/health

# Example response
{
  "status": "healthy",
  "components": {
    "plan": "operational",
    "draft": "operational",
    "critic": "operational",
    "revise": "operational"
  },
  "verifiers": {
    "code": "enabled",
    "math": "enabled",
    "retrieval": "enabled"
  },
  "stats": {
    "avg_rounds": 2.3,
    "avg_confidence": 0.89,
    "avg_duration_ms": 1250
  }
}
```

### Operational Procedures

#### Tuning Confidence Threshold (τ)

```bash
# Too many max rounds reached? Lower threshold
# Current: 0.85, Try: 0.80
sed -i 's/SELF_LOOP_CONFIDENCE_THRESHOLD=0.85/SELF_LOOP_CONFIDENCE_THRESHOLD=0.80/' .env
docker-compose restart api

# Monitor impact
watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=self_loop_max_rounds_reached_total'

# Too many low-quality responses? Raise threshold
sed -i 's/SELF_LOOP_CONFIDENCE_THRESHOLD=0.80/SELF_LOOP_CONFIDENCE_THRESHOLD=0.90/' .env
docker-compose restart api
```

#### Adjusting Max Rounds

```bash
# High latency issues? Reduce max rounds
sed -i 's/SELF_LOOP_MAX_ROUNDS=5/SELF_LOOP_MAX_ROUNDS=3/' .env
docker-compose restart api

# Complex queries failing? Increase max rounds
sed -i 's/SELF_LOOP_MAX_ROUNDS=3/SELF_LOOP_MAX_ROUNDS=7/' .env
docker-compose restart api

# Monitor round distribution
curl -s http://localhost:9090/api/v1/query?query='histogram_quantile(0.5, self_loop_rounds_total_bucket)'
```

#### Verifier Management

```bash
# Disable specific verifier if causing issues
sed -i 's/SELF_LOOP_ENABLE_CODE_EXEC=true/SELF_LOOP_ENABLE_CODE_EXEC=false/' .env
docker-compose restart api

# Check verifier performance
curl http://localhost:8000/api/v1/verifiers/stats

# Example response
{
  "code_verifier": {
    "total_checks": 1523,
    "pass_rate": 0.87,
    "avg_duration_ms": 450,
    "last_error": null
  },
  "math_verifier": {
    "total_checks": 892,
    "pass_rate": 0.93,
    "avg_duration_ms": 120,
    "last_error": null
  },
  "retrieval_verifier": {
    "total_checks": 2341,
    "pass_rate": 0.91,
    "avg_duration_ms": 230,
    "last_error": null
  }
}
```

### Troubleshooting Self-Loop Issues

#### High Latency in Self-Loop

```bash
# 1. Check average rounds
curl -s http://localhost:9090/api/v1/query?query='avg(self_loop_rounds_total)'

# If avg > 3, investigate why queries need multiple rounds
docker-compose logs api | grep "self_loop.*round"

# 2. Profile specific query types
curl http://localhost:8000/api/v1/self-loop/profile?query_type=math

# 3. Optimize verifier execution
# Run verifiers in parallel (if not already)
sed -i 's/SELF_LOOP_PARALLEL_VERIFY=false/SELF_LOOP_PARALLEL_VERIFY=true/' .env
docker-compose restart api

# 4. Check model tier selection
# Ensure lighter models handle simple queries
docker-compose logs api | grep "model_tier"
```

#### Low Confidence Scores

```bash
# 1. Check verifier failure patterns
curl http://localhost:9090/api/v1/query?query='rate(self_loop_verifier_failures_total[1h]) by (verifier_type)'

# 2. Analyze failed verifications
docker-compose logs api | grep "verifier_failed" | tail -50

# 3. Review retrieval quality
curl http://localhost:8000/api/v1/retrieval/debug?query="example query"

# 4. Check if models are appropriate for query complexity
# Upgrade to higher tier if needed
sed -i 's/DEFAULT_MODEL_TIER=1/DEFAULT_MODEL_TIER=2/' .env
docker-compose restart api
```

#### Self-Loop Not Stopping (Max Rounds)

```bash
# 1. Identify problematic query patterns
docker-compose logs api | grep "max_rounds_reached" | tail -20

# 2. Check if verifiers are too strict
curl http://localhost:8000/api/v1/verifiers/thresholds

# 3. Adjust verifier sensitivity
# Example: Relax math verifier tolerance
sed -i 's/MATH_VERIFIER_TOLERANCE=0.01/MATH_VERIFIER_TOLERANCE=0.05/' .env
docker-compose restart api

# 4. Enable debug logging
sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' .env
docker-compose restart api
docker-compose logs -f api | grep "self_loop_iteration"
```

#### Code Execution Failures

```bash
# 1. Check sandbox status
curl http://localhost:8000/api/v1/sandbox/health

# 2. Review code execution logs
docker-compose logs api | grep "code_execution" | tail -30

# 3. Test code verifier directly
curl -X POST http://localhost:8000/api/v1/test/code-verifier \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2+2)"}'

# 4. Check sandbox resource limits
docker stats liquid_hive_sandbox

# 5. Restart sandbox if needed
docker-compose restart sandbox
```

### Performance Optimization

#### Self-Loop Caching

```bash
# Enable result caching for similar queries
sed -i 's/SELF_LOOP_CACHE_ENABLED=false/SELF_LOOP_CACHE_ENABLED=true/' .env
sed -i 's/SELF_LOOP_CACHE_TTL=3600/SELF_LOOP_CACHE_TTL=7200/' .env
docker-compose restart api

# Monitor cache hit rate
curl http://localhost:9090/api/v1/query?query='rate(self_loop_cache_hits_total[5m]) / rate(self_loop_cache_requests_total[5m])'

# Clear cache if needed
curl -X POST http://localhost:8000/api/v1/cache/clear?scope=self_loop
```

#### Model Tier Optimization

```bash
# Analyze tier utilization
curl http://localhost:9090/api/v1/query?query='sum by (tier) (rate(model_requests_total[1h]))'

# Adjust tier routing thresholds
# config/model_router.yaml
tier_selection:
  tier1:  # Fast, simple queries
    max_tokens: 512
    complexity_threshold: 0.3
  tier2:  # Medium complexity
    max_tokens: 2048
    complexity_threshold: 0.7
  tier3:  # Complex reasoning
    max_tokens: 8192
    complexity_threshold: 1.0

# Apply configuration
docker-compose restart api
```

#### Parallel Verifier Execution

```bash
# Enable parallel verification
sed -i 's/SELF_LOOP_PARALLEL_VERIFY=false/SELF_LOOP_PARALLEL_VERIFY=true/' .env
sed -i 's/SELF_LOOP_VERIFIER_THREADS=1/SELF_LOOP_VERIFIER_THREADS=3/' .env
docker-compose restart api

# Monitor performance improvement
# Before and after comparison
curl http://localhost:9090/api/v1/query?query='histogram_quantile(0.95, rate(self_loop_duration_seconds_bucket[5m]))'
```

### Self-Loop Testing & Validation

#### Integration Tests

```bash
# Run Self-Loop test suite
docker-compose exec api pytest tests/self_loop/ -v

# Test specific scenarios
docker-compose exec api pytest tests/self_loop/test_math_reasoning.py -v
docker-compose exec api pytest tests/self_loop/test_code_generation.py -v
docker-compose exec api pytest tests/self_loop/test_retrieval_grounding.py -v
```

#### Load Testing Self-Loop

```bash
# Run load test with realistic queries
locust -f tests/load/self_loop_locustfile.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m

# Monitor during load test
watch -n 2 'curl -s http://localhost:9090/api/v1/query?query=self_loop_duration_seconds'
```

#### A/B Testing Configuration Changes

```bash
# Deploy canary with new settings
# 1. Create canary environment
cp .env .env.canary
sed -i 's/SELF_LOOP_MAX_ROUNDS=5/SELF_LOOP_MAX_ROUNDS=3/' .env.canary

# 2. Deploy canary instance
docker-compose -f docker-compose.canary.yml up -d

# 3. Route 10% traffic to canary (nginx configuration)
# 4. Compare metrics between stable and canary

# Stable metrics
curl 'http://localhost:9090/api/v1/query?query=avg(self_loop_duration_seconds{instance="stable"})'

# Canary metrics
curl 'http://localhost:9090/api/v1/query?query=avg(self_loop_duration_seconds{instance="canary"})'
```

### Advanced Debugging

#### Enable Self-Loop Tracing

```bash
# Enable detailed trace logging
sed -i 's/SELF_LOOP_TRACE_ENABLED=false/SELF_LOOP_TRACE_ENABLED=true/' .env
docker-compose restart api

# View trace logs
docker-compose logs -f api | grep "TRACE"

# Example trace output:
# [TRACE] self_loop.plan: query_id=abc123, complexity=0.7, selected_tier=2
# [TRACE] self_loop.draft: round=1, model=tier2, tokens=450, duration_ms=1200
# [TRACE] self_loop.critic: round=1, code_verify=PASS, math_verify=PASS, retrieval_verify=FAIL, confidence=0.65
# [TRACE] self_loop.revise: round=1, feedback="Need better retrieval context", action=re_retrieve
# [TRACE] self_loop.draft: round=2, model=tier2, tokens=520, duration_ms=1100
# [TRACE] self_loop.critic: round=2, code_verify=PASS, math_verify=PASS, retrieval_verify=PASS, confidence=0.92
# [TRACE] self_loop.complete: rounds=2, final_confidence=0.92, total_duration_ms=2850
```

#### Query-Level Analysis

```bash
# Analyze specific query execution
curl -X POST http://localhost:8000/api/v1/self-loop/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the derivative of x^2 + 3x + 2",
    "trace": true,
    "return_intermediate": true
  }'

# Response includes full execution trace
{
  "query_id": "abc123",
  "rounds": [
    {
      "round": 1,
      "plan": {...},
      "draft": {...},
      "critic": {...},
      "revise": {...}
    },
    {
      "round": 2,
      "plan": {...},
      "draft": {...},
      "critic": {...}
    }
  ],
  "final_answer": "2x + 3",
  "confidence": 0.95,
  "total_duration_ms": 1850
}
```

## 🚀 Deployment Procedures

### Pre-deployment Checklist

```bash
# 1. System Requirements Check
./scripts/check-requirements.sh

# 2. Environment Configuration
cp .env.example .env
# Edit .env with production values

# 3. SSL Certificates (Production)
# Place certificates in nginx/ssl/
ls -la nginx/ssl/cert.pem nginx/ssl/key.pem

# 4. Database Backup (if upgrading)
./scripts/backup.sh

# 5. Resource Availability
df -h  # Check disk space
free -h  # Check memory
nvidia-smi  # Check GPU
```

### Production Deployment

```bash
# 1. Deploy with automated script
./scripts/deploy.sh production

# 2. Manual deployment (if needed)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify deployment
./scripts/health-check.sh
```

### Rolling Updates

```bash
# 1. Update API service only
docker-compose -f docker-compose.prod.yml up -d --no-deps api

# 2. Update frontend only
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend

# 3. Update specific vLLM tier
docker-compose -f docker-compose.prod.yml up -d --no-deps vllm_tier2
```

### Blue-Green Deployment

```bash
# 1. Prepare green environment
cp docker-compose.prod.yml docker-compose.green.yml
# Modify ports in green compose file

# 2. Deploy green environment
docker-compose -f docker-compose.green.yml up -d

# 3. Test green environment
curl http://localhost:8080/health

# 4. Switch traffic (update nginx config)
# 5. Stop blue environment
docker-compose -f docker-compose.prod.yml down
```

## 📊 Monitoring & Alerting

### Grafana Dashboards

#### System Overview Dashboard
- **URL**: http://localhost:3001/d/system-overview
- **Metrics**: CPU, Memory, Disk, Network
- **Alerts**: Resource thresholds, service availability

#### API Performance Dashboard
- **URL**: http://localhost:3001/d/api-performance
- **Metrics**: Request rate, latency, error rate
- **Alerts**: High latency, error spikes

#### Model Performance Dashboard
- **URL**: http://localhost:3001/d/model-performance
- **Metrics**: Inference time, GPU utilization, queue length
- **Alerts**: Model failures, high latency

### Prometheus Alerts

#### Critical Alerts
```yaml
# Service Down
- alert: ServiceDown
  expr: up == 0
  for: 1m
  severity: critical

# High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 2m
  severity: critical

# Database Connection Issues
- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  for: 1m
  severity: critical
```

#### Warning Alerts
```yaml
# High Latency
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  severity: warning

# High Memory Usage
- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
  for: 5m
  severity: warning
```

### Log Management

#### Log Locations
```bash
# Application logs
./logs/api/app.log
./logs/frontend/next.log
./logs/nginx/access.log
./logs/nginx/error.log

# Container logs
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f vllm_tier1
```

#### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/liquid-hive

# Manual log rotation
sudo logrotate -f /etc/logrotate.d/liquid-hive
```

#### Centralized Logging (Optional)
```bash
# ELK Stack deployment
docker-compose -f docker-compose.logging.yml up -d

# Fluentd configuration
# Configure log forwarding to external systems
```

## 💾 Backup & Recovery

### Automated Backup Schedule

```bash
# Daily backups at 2 AM
0 2 * * * /path/to/liquid-hive/scripts/backup.sh

# Weekly full backups on Sunday at 1 AM
0 1 * * 0 /path/to/liquid-hive/scripts/backup.sh --full

# Monthly archive to cold storage
0 0 1 * * /path/to/liquid-hive/scripts/archive.sh
```

### Backup Components

#### Database Backups
```bash
# PostgreSQL backup
pg_dump -h postgres -U liquid_hive -d liquid_hive \
  --format=custom --file=postgres_backup.dump

# Qdrant backup
docker exec liquid_hive_qdrant qdrant-cli snapshot create

# Elasticsearch backup
curl -X PUT "elasticsearch:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)"
```

#### Configuration Backups
```bash
# Backup configuration files
tar -czf config_backup.tar.gz \
  config/ nginx/ monitoring/ .env docker-compose.prod.yml
```

#### Model Checkpoints
```bash
# Backup fine-tuned models (if any)
tar -czf models_backup.tar.gz ~/.cache/huggingface/
```

### Recovery Procedures

#### Database Recovery
```bash
# PostgreSQL recovery
pg_restore -h postgres -U liquid_hive -d liquid_hive \
  --clean --if-exists postgres_backup.dump

# Qdrant recovery
docker exec liquid_hive_qdrant qdrant-cli snapshot restore snapshot_name

# Elasticsearch recovery
curl -X POST "elasticsearch:9200/_snapshot/backup_repo/snapshot_name/_restore"
```

#### Full System Recovery
```bash
# 1. Stop all services
docker-compose -f docker-compose.prod.yml down

# 2. Restore data volumes
docker volume rm liquid_hive_postgres_data
docker volume rm liquid_hive_qdrant_data
docker volume rm liquid_hive_elasticsearch_data

# 3. Run restore script
./scripts/restore.sh 20241201_020000

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Backup Verification

```bash
# Test backup integrity
./scripts/verify-backup.sh latest

# Restore to test environment
./scripts/restore.sh latest --environment=test
```

## ⚡ Scaling & Performance

### Horizontal Scaling

#### API Service Scaling
```bash
# Scale API service
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Update nginx upstream configuration
# Add additional API instances to nginx.conf
```

#### Model Service Scaling
```bash
# Scale specific model tier
docker-compose -f docker-compose.prod.yml up -d --scale vllm_tier2=2

# Load balancing configuration
# Update model routing logic in API service
```

### Vertical Scaling

#### Resource Allocation
```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

#### GPU Allocation
```yaml
# Multiple GPU allocation
services:
  vllm_tier3:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
```

### Performance Optimization

#### Database Optimization
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

#### Cache Optimization
```bash
# Redis optimization
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Model Optimization
```python
# vLLM optimization parameters
TENSOR_PARALLEL_SIZE=2
GPU_MEMORY_UTILIZATION=0.9
MAX_MODEL_LEN=4096
QUANTIZATION=awq
```

### Auto-scaling (Kubernetes)

```yaml
# HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: liquid-hive-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: liquid-hive-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔒 Security Operations

### Security Monitoring

#### Failed Authentication Attempts
```bash
# Monitor failed logins
grep "authentication failed" logs/api/app.log | tail -20

# Block suspicious IPs
iptables -A INPUT -s SUSPICIOUS_IP -j DROP
```

#### Rate Limiting Monitoring
```bash
# Check rate limit violations
curl http://localhost:9090/api/v1/query?query=rate_limit_exceeded_total

# Adjust rate limits
# Update RATE_LIMIT_REQUESTS in .env
```

### SSL Certificate Management

#### Certificate Renewal
```bash
# Let's Encrypt renewal
certbot renew --nginx

# Manual certificate update
cp new_cert.pem nginx/ssl/cert.pem
cp new_key.pem nginx/ssl/key.pem
docker-compose restart nginx
```

#### Certificate Monitoring
```bash
# Check certificate expiry
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Automated monitoring
echo "0 0 * * * /path/to/check-ssl-expiry.sh" | crontab -
```

### Security Auditing

#### Access Log Analysis
```bash
# Analyze nginx access logs
awk '{print $1}' logs/nginx/access.log | sort | uniq -c | sort -nr | head -20

# Check for suspicious patterns
grep -E "(sql|script|alert)" logs/nginx/access.log
```

#### Vulnerability Scanning
```bash
# Container vulnerability scan
trivy image liquid-hive-api:latest

# Dependency vulnerability scan
safety check -r requirements.txt
```

### Incident Response

#### Security Incident Checklist
1. **Identify**: Detect and analyze the incident
2. **Contain**: Isolate affected systems
3. **Eradicate**: Remove the threat
4. **Recover**: Restore normal operations
5. **Learn**: Document and improve

#### Emergency Procedures
```bash
# Emergency shutdown
docker-compose -f docker-compose.prod.yml down

# Block all traffic
iptables -A INPUT -j DROP
iptables -A OUTPUT -j DROP

# Isolate database
docker-compose stop postgres
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs service_name

# Check resource usage
docker stats

# Check port conflicts
netstat -tulpn | grep :8000
```

#### High Memory Usage
```bash
# Identify memory-hungry processes
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Restart memory-intensive services
docker-compose restart vllm_tier3
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check connection pool
docker-compose exec postgres psql -U liquid_hive -c "SELECT * FROM pg_stat_activity;"

# Reset connections
docker-compose restart api
```

#### Model Loading Failures
```bash
# Check GPU availability
nvidia-smi

# Check HuggingFace token
docker-compose exec vllm_tier1 env | grep HF_TOKEN

# Clear model cache
docker volume rm liquid_hive_model_cache
```

### Performance Issues

#### High API Latency
```bash
# Check API metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# Profile API endpoints
docker-compose exec api python -m cProfile -o profile.stats app.py

# Check database query performance
docker-compose exec postgres psql -U liquid_hive -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### Model Inference Slow
```bash
# Check GPU utilization
nvidia-smi -l 1

# Check model queue length
curl http://localhost:8001/metrics | grep queue

# Optimize model parameters
# Reduce MAX_MODEL_LEN or increase TENSOR_PARALLEL_SIZE
```

### Network Issues

#### Connection Timeouts
```bash
# Check network connectivity
docker-compose exec api ping elasticsearch

# Check DNS resolution
docker-compose exec api nslookup qdrant

# Check firewall rules
iptables -L
```

#### Load Balancer Issues
```bash
# Check nginx status
docker-compose exec nginx nginx -t

# Reload nginx configuration
docker-compose exec nginx nginx -s reload

# Check upstream health
curl -H "Host: yourdomain.com" http://localhost/health
```

## 🔄 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
# Check system health
./scripts/health-check.sh

# Review logs for errors
grep -i error logs/api/app.log | tail -20

# Check disk space
df -h

# Verify backups
ls -la backups/ | tail -5
```

#### Weekly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete

# Optimize databases
docker-compose exec postgres psql -U liquid_hive -c "VACUUM ANALYZE;"

# Check SSL certificate expiry
openssl x509 -in nginx/ssl/cert.pem -noout -dates
```

#### Monthly Tasks
```bash
# Full system backup
./scripts/backup.sh --full

# Security audit
./scripts/security-audit.sh

# Performance review
./scripts/performance-report.sh

# Update dependencies
pip-review --local --interactive
```

### Database Maintenance

#### PostgreSQL Maintenance
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE liquid_hive;

-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Qdrant Maintenance
```bash
# Optimize collections
curl -X POST "http://localhost:6333/collections/documents/index"

# Check collection info
curl "http://localhost:6333/collections/documents"

# Compact storage
docker exec liquid_hive_qdrant qdrant-cli collection optimize documents
```

#### Elasticsearch Maintenance
```bash
# Force merge indices
curl -X POST "localhost:9200/_forcemerge?max_num_segments=1"

# Delete old indices
curl -X DELETE "localhost:9200/logs-$(date -d '30 days ago' +%Y.%m.%d)"

# Check cluster health
curl "localhost:9200/_cluster/health?pretty"
```

### Model Management

#### Model Updates
```bash
# Update model versions in .env
VLLM_TIER2_MODEL=LiquidAI/LFM2-1.2B-Tool:v2

# Pull new models
docker-compose pull vllm_tier2

# Rolling update
docker-compose up -d --no-deps vllm_tier2
```

#### Model Cache Management
```bash
# Clear model cache
docker volume rm liquid_hive_model_cache

# Check cache size
du -sh ~/.cache/huggingface/

# Prune unused models
huggingface-cli delete-cache
```

## 🚨 Disaster Recovery

### Disaster Recovery Plan

#### Recovery Time Objectives (RTO)
- **Critical Services**: 15 minutes
- **Full System**: 1 hour
- **Data Recovery**: 4 hours

#### Recovery Point Objectives (RPO)
- **Database**: 1 hour (hourly backups)
- **Configuration**: 24 hours (daily backups)
- **Models**: 7 days (weekly backups)

### Disaster Scenarios

#### Complete System Failure
```bash
# 1. Assess damage
./scripts/assess-damage.sh

# 2. Provision new infrastructure
./scripts/provision-infrastructure.sh

# 3. Restore from backups
./scripts/restore.sh latest --full

# 4. Verify system integrity
./scripts/verify-system.sh

# 5. Resume operations
./scripts/resume-operations.sh
```

#### Data Corruption
```bash
# 1. Stop affected services
docker-compose stop postgres qdrant elasticsearch

# 2. Assess corruption extent
./scripts/check-data-integrity.sh

# 3. Restore from clean backup
./scripts/restore.sh --data-only

# 4. Verify data integrity
./scripts/verify-data.sh

# 5. Restart services
docker-compose start postgres qdrant elasticsearch
```

#### Security Breach
```bash
# 1. Immediate containment
./scripts/emergency-shutdown.sh

# 2. Forensic analysis
./scripts/forensic-analysis.sh

# 3. Clean restoration
./scripts/clean-restore.sh

# 4. Security hardening
./scripts/security-hardening.sh

# 5. Gradual service restoration
./scripts/gradual-restore.sh
```

### Business Continuity

#### Failover Procedures
```bash
# Activate standby system
./scripts/activate-standby.sh

# Update DNS records
./scripts/update-dns.sh --failover

# Notify stakeholders
./scripts/notify-failover.sh
```

#### Communication Plan
1. **Internal Team**: Slack/Teams notification
2. **Management**: Email/Phone notification
3. **Users**: Status page update
4. **Partners**: API status notification

## 🔄 CI/CD Pipeline

### Pipeline Stages

#### 1. Code Quality
```yaml
# .github/workflows/ci.yml
- name: Lint Code
  run: |
    flake8 .
    black --check .
    isort --check-only .

- name: Security Scan
  run: |
    bandit -r .
    safety check
```

#### 2. Testing
```yaml
- name: Unit Tests
  run: pytest tests/unit/ -v --cov

- name: Integration Tests
  run: pytest tests/integration/ -v

- name: Load Tests
  run: locust -f tests/load/locustfile.py --headless
```

#### 3. Build & Push
```yaml
- name: Build Images
  run: |
    docker build -t liquid-hive-api:${{ github.sha }} .
    docker build -t liquid-hive-frontend:${{ github.sha }} ./frontend

- name: Push to Registry
  run: |
    docker push liquid-hive-api:${{ github.sha }}
    docker push liquid-hive-frontend:${{ github.sha }}
```

#### 4. Deployment
```yaml
- name: Deploy to Staging
  run: |
    ./scripts/deploy.sh staging ${{ github.sha }}

- name: Deploy to Production
  run: |
    ./scripts/deploy.sh production ${{ github.sha }}
```

### Deployment Strategies

#### Blue-Green Deployment
```bash
# Deploy to green environment
./scripts/deploy-green.sh

# Run smoke tests
./scripts/smoke-tests.sh green

# Switch traffic
./scripts/switch-traffic.sh green

# Monitor and rollback if needed
./scripts/monitor-deployment.sh
```

#### Canary Deployment
```bash
# Deploy canary version (10% traffic)
./scripts/deploy-canary.sh 10

# Monitor metrics
./scripts/monitor-canary.sh

# Gradually increase traffic
./scripts/increase-canary.sh 50
./scripts/increase-canary.sh 100
```

### Rollback Procedures

#### Automatic Rollback
```bash
# Configure automatic rollback triggers
# - Error rate > 5%
# - Latency > 2s
# - Health check failures

./scripts/configure-auto-rollback.sh
```

#### Manual Rollback
```bash
# Rollback to previous version
./scripts/rollback.sh previous

# Rollback to specific version
./scripts/rollback.sh v1.2.3

# Emergency rollback
./scripts/emergency-rollback.sh
```

---

## 📞 Emergency Contacts

### On-Call Rotation
- **Primary**: DevOps Engineer
- **Secondary**: Backend Developer
- **Escalation**: Technical Lead

### Contact Information
- **Slack**: #liquid-hive-alerts
- **PagerDuty**: liquid-hive-oncall
- **Email**: ops@liquidhive.com

### Escalation Matrix
1. **Level 1**: Service degradation (15 min response)
2. **Level 2**: Service outage (5 min response)
3. **Level 3**: Security incident (immediate response)

---

*This operations manual should be reviewed and updated quarterly to ensure accuracy and completeness.*
