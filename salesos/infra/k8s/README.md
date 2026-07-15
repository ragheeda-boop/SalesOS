# SalesOS Kubernetes Deployment

## Requirements

- Kubernetes cluster v1.28+
- kubectl v1.28+
- kustomize v5.0+ (built into kubectl since v1.21)
- Helm v3.x (for operators)
- cert-manager v1.12+ (for TLS certificates)
- ingress-nginx controller
- (Optional) Sealed Secrets or External Secrets Operator

## Prerequisites Installation

```bash
# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Install Sealed Secrets (optional)
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm upgrade --install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system
```

## Secrets Management

### Option A: Sealed Secrets (recommended for GitOps)
```bash
# Create a sealed secret from the template
kubeseal --namespace salesos --format yaml \
  < infra/k8s/secrets.yaml \
  > infra/k8s/sealed-secrets.yaml

# Apply
kubectl apply -f infra/k8s/sealed-secrets.yaml
```

### Option B: External Secrets Operator
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace

# Create an ExternalSecret CRD referencing AWS/GCP/Azure secrets manager
# See: https://external-secrets.io/v0.8.1/provider/
```

### Option C: Manual (for testing only)
```bash
# Edit infra/k8s/secrets.yaml with real values, then apply
kubectl apply -f infra/k8s/secrets.yaml
```

## Deployment Steps

### 1. Apply all manifests

```bash
# Preview
kubectl kustomize infra/k8s/

# Deploy
kubectl apply -k infra/k8s/
```

### 2. Verify deployment

```bash
# Check pods
kubectl get pods -n salesos -w

# Check services
kubectl get svc -n salesos

# Check ingress
kubectl get ingress -n salesos
```

### 3. Set up ClusterIssuer (cert-manager)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@salesos.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

```bash
kubectl apply -f cluster-issuer.yaml
```

## Ingress Configuration

| Domain | Service | Port |
|--------|---------|------|
| `api.salesos.com` | backend | 8000 |
| `app.salesos.com` | frontend | 3000 |

Add these records to your DNS provider:
- `api.salesos.com` → Ingress Controller Load Balancer IP
- `app.salesos.com` → Ingress Controller Load Balancer IP

## Namespace Structure

```
salesos/
├── postgres/         # StatefulSet + Headless Service
├── neo4j/            # StatefulSet + Headless Service
├── redis/            # Deployment + PVC
├── backend/          # Deployment (3 replicas) + HPA (3-10)
├── frontend/         # Deployment (3 replicas) + HPA (3-8)
├── kafka/            # StatefulSet + Zookeeper
├── prometheus/       # Deployment + ConfigMap + RBAC
└── grafana/          # Deployment + ConfigMap + PVC
```

## Resource Limits

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Storage |
|---------|-------------|-----------|----------------|--------------|---------|
| postgres | 500m | 2 | 1Gi | 2Gi | 50Gi |
| neo4j | 1 | 2 | 2Gi | 4Gi | 20Gi |
| redis | 100m | 500m | 128Mi | 256Mi | 5Gi |
| backend | 500m | 2 | 512Mi | 1Gi | - |
| frontend | 200m | 1 | 256Mi | 512Mi | - |
| kafka | 250m | 1 | 512Mi | 1Gi | 20Gi |
| zookeeper | 100m | 500m | 256Mi | 512Mi | 5Gi |
| prometheus | 250m | 1 | 512Mi | 1Gi | 50Gi |
| grafana | 100m | 500m | 256Mi | 512Mi | 10Gi |

## Horizontal Pod Autoscaler

| Deployment | Min | Max | CPU Target | Memory Target |
|------------|-----|-----|------------|---------------|
| backend | 3 | 10 | 70% | 80% |
| frontend | 3 | 8 | 70% | 80% |

## Monitoring

Prometheus is pre-configured with:
- Kubernetes SD for automatic service discovery
- ServiceMonitor-ready (annotations on backend pods)
- Pre-loaded alerting rules (BackendDown, HighErrorRate, etc.)

Grafana is pre-configured with:
- Prometheus datasource (auto-configured)
- Dashboard provisioning ready

Access:
- Prometheus: `prometheus.salesos:9090`
- Grafana: `grafana.salesos:3000` (or via ingress at `monitoring.salesos.com`)

## Production Recommendations

### cert-manager
- Required for automatic TLS certificate management
- Uses Let's Encrypt for production certificates
- Configure ClusterIssuer before applying ingress manifests

### external-dns
- Automatically manages DNS records for Kubernetes ingresses
- Works with Cloudflare, Route53, Google Cloud DNS
- Install: `helm install external-dns ...`

### Monitoring Stack (kube-prometheus-stack)
- Install for node-level monitoring (node-exporter, kube-state-metrics)
- Provides cluster-wide dashboards and alerts

### Backup Strategy

1. **PostgreSQL**: Use `pg_dump` with a CronJob
2. **Neo4j**: Use `neo4j-admin dump` with a CronJob
3. **PV Snapshots**: Use CSI VolumeSnapshots if supported

Example backup CronJob:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16
              command: ["pg_dump", "-h", "postgres", "-U", "salesos", "-d", "salesos", "-f", "/backups/db-$(date +%Y%m%d).sql"]
          restartPolicy: OnFailure
```

### Network Policies
Apply network policies to restrict pod-to-pod communication per service.

### Service Mesh (Istio/Linkerd)
Consider for production:
- mTLS between all services
- Traffic splitting for canary deployments
- Detailed telemetry per request

### Pod Disruption Budgets
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: backend
```

## CI/CD Pipeline

The production deployment workflow (`.github/workflows/deploy-production.yml`) follows:

1. **Build & Push**: Build images, tag with git SHA, push to GHCR
2. **Deploy**: `kubectl set image` on staging → then production via kustomize
3. **Smoke Tests**: HTTP health checks, DB connectivity, API endpoints
4. **Rollback**: `kubectl rollout undo` on failure
5. **Notify**: Slack/Teams/GitHub commit comment
