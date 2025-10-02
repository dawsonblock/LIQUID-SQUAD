
# Kubernetes Deployment for LIQUID HIVE 25

This directory contains Kubernetes manifests for deploying LIQUID HIVE 25 in production.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- kustomize (built into kubectl)
- Ingress controller (nginx recommended)
- cert-manager (for TLS certificates)

## Quick Start

### Development Deployment

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/dev

# Check deployment status
kubectl get pods -n liquid-hive-dev

# View logs
kubectl logs -f deployment/dev-liquid-hive-api -n liquid-hive-dev
```

### Production Deployment

```bash
# Update secrets first
kubectl create secret generic liquid-hive-secrets \
  --from-literal=POSTGRES_PASSWORD=<strong-password> \
  --from-literal=JWT_SECRET_KEY=<strong-secret> \
  -n liquid-hive --dry-run=client -o yaml | kubectl apply -f -

# Apply production configuration
kubectl apply -k k8s/overlays/prod

# Check deployment status
kubectl get pods -n liquid-hive

# View services
kubectl get svc -n liquid-hive
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Ingress (NGINX)                      │
│              liquid-hive.example.com                    │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼─────┐    ┌─────▼────┐
   │ Frontend │    │   API    │
   │ (Next.js)│    │ (FastAPI)│
   │  x2      │    │  x3-10   │
   └──────────┘    └─────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐    ┌─────▼────┐    ┌─────▼────┐
   │ Postgres│    │  Redis   │    │  Qdrant  │
   │         │    │          │    │          │
   └─────────┘    └──────────┘    └──────────┘
```

## Components

### Core Services

- **API**: FastAPI backend with auto-scaling (3-10 replicas)
- **Frontend**: Next.js UI (2 replicas)
- **PostgreSQL**: Primary database (1 replica)
- **Redis**: Caching and rate limiting (1 replica)
- **Qdrant**: Vector database (1 replica)

### Storage

- Persistent volumes for databases
- Automatic volume provisioning
- Backup-ready configuration

### Networking

- Internal ClusterIP services
- Ingress with TLS termination
- Network policies (optional)

### Scaling

- Horizontal Pod Autoscaler for API
- CPU and memory-based scaling
- Min 3, max 10 replicas (dev)
- Min 5, max 20 replicas (prod)

## Configuration

### Secrets

Update `k8s/base/secrets.yaml` with production values:

```yaml
POSTGRES_PASSWORD: <strong-password>
JWT_SECRET_KEY: <strong-secret-key>
DEEPSEEK_API_KEY: <api-key-if-needed>
```

### ConfigMap

Modify `k8s/base/configmap.yaml` for environment-specific settings:

```yaml
CORS_ALLOW_ORIGINS: "https://your-domain.com"
RATE_LIMIT_REQUESTS: "100"
```

### Ingress

Update `k8s/base/ingress.yaml` with your domain:

```yaml
spec:
  tls:
  - hosts:
    - your-domain.com
  rules:
  - host: your-domain.com
```

## Monitoring

### Health Checks

```bash
# Check API health
kubectl exec -it deployment/liquid-hive-api -n liquid-hive -- curl http://localhost:8000/healthz

# Check readiness
kubectl exec -it deployment/liquid-hive-api -n liquid-hive -- curl http://localhost:8000/readyz
```

### Logs

```bash
# API logs
kubectl logs -f deployment/liquid-hive-api -n liquid-hive

# Frontend logs
kubectl logs -f deployment/liquid-hive-frontend -n liquid-hive

# All pods
kubectl logs -f -l app=liquid-hive-api -n liquid-hive
```

### Metrics

```bash
# Pod metrics
kubectl top pods -n liquid-hive

# Node metrics
kubectl top nodes
```

## Scaling

### Manual Scaling

```bash
# Scale API
kubectl scale deployment liquid-hive-api --replicas=5 -n liquid-hive

# Scale frontend
kubectl scale deployment liquid-hive-frontend --replicas=3 -n liquid-hive
```

### Auto-scaling

HPA is configured for the API deployment:

```bash
# View HPA status
kubectl get hpa -n liquid-hive

# Describe HPA
kubectl describe hpa liquid-hive-api-hpa -n liquid-hive
```

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL
kubectl exec -it deployment/postgres -n liquid-hive -- \
  pg_dump -U liquid_hive liquid_hive > backup.sql

# Restore PostgreSQL
kubectl exec -i deployment/postgres -n liquid-hive -- \
  psql -U liquid_hive liquid_hive < backup.sql
```

### Qdrant Backup

```bash
# Create snapshot
kubectl exec -it deployment/qdrant -n liquid-hive -- \
  curl -X POST http://localhost:6333/collections/documents/snapshots

# Download snapshot
kubectl cp liquid-hive/qdrant-pod:/qdrant/storage/snapshots ./snapshots
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n liquid-hive

# Check events
kubectl get events -n liquid-hive --sort-by='.lastTimestamp'
```

### Service Not Accessible

```bash
# Check service
kubectl get svc -n liquid-hive

# Test service internally
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n liquid-hive -- \
  curl http://liquid-hive-api-service:8000/healthz
```

### Ingress Issues

```bash
# Check ingress
kubectl describe ingress liquid-hive-ingress -n liquid-hive

# Check ingress controller logs
kubectl logs -f -n ingress-nginx deployment/ingress-nginx-controller
```

## Cleanup

```bash
# Delete development deployment
kubectl delete -k k8s/overlays/dev

# Delete production deployment
kubectl delete -k k8s/overlays/prod

# Delete namespace (removes everything)
kubectl delete namespace liquid-hive
```

## Security Best Practices

1. **Secrets Management**: Use external secret managers (Vault, AWS Secrets Manager)
2. **Network Policies**: Implement pod-to-pod communication restrictions
3. **RBAC**: Configure role-based access control
4. **Pod Security**: Use security contexts and pod security policies
5. **Image Scanning**: Scan container images for vulnerabilities
6. **TLS**: Enable TLS for all external communications
7. **Resource Limits**: Set appropriate resource requests and limits

## Production Checklist

- [ ] Update all secrets with strong values
- [ ] Configure domain and TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Test disaster recovery procedures
- [ ] Review and apply network policies
- [ ] Configure resource quotas
- [ ] Set up log aggregation
- [ ] Enable audit logging
- [ ] Document runbooks
