# Kubernetes Deployment

Deploy SolanaLM on Kubernetes for production-grade scalability.

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x (optional)
- GPU nodes (optional, for inference)

## Quick Start

```bash
# Generate Kubernetes manifests
python deployment/orchestrator.py --target kubernetes --replicas 3

# Apply manifests
kubectl apply -f k8s-manifests/

# Check deployment
kubectl get pods -n solanalm
```

## Namespace Setup

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: solanalm
  labels:
    app: solanalm
```

```bash
kubectl apply -f k8s/namespace.yaml
```

## Gateway Deployment

```yaml
# k8s/gateway/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: solanalm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: solanalm/gateway:latest
        ports:
        - containerPort: 8001
        env:
        - name: SOLANA_NETWORK
          valueFrom:
            configMapKeyRef:
              name: solanalm-config
              key: SOLANA_NETWORK
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: solanalm-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: solanalm-secrets
              key: REDIS_URL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: solanalm
spec:
  selector:
    app: gateway
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

## Inference Node Deployment

```yaml
# k8s/inference/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-node
  namespace: solanalm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: inference-node
  template:
    metadata:
      labels:
        app: inference-node
    spec:
      containers:
      - name: inference
        image: solanalm/inference-node:latest
        ports:
        - containerPort: 8100
        env:
        - name: NODE_TYPE
          value: "inference"
        - name: GATEWAY_URL
          value: "http://gateway:8001"
        - name: WALLET_ADDRESS
          valueFrom:
            secretKeyRef:
              name: solanalm-secrets
              key: WALLET_ADDRESS
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
            nvidia.com/gpu: 1
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: model-cache
          mountPath: /app/models
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      nodeSelector:
        gpu: "true"
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

## Training Node Deployment

```yaml
# k8s/training/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: training-node
  namespace: solanalm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: training-node
  template:
    metadata:
      labels:
        app: training-node
    spec:
      containers:
      - name: training
        image: solanalm/training-node:latest
        ports:
        - containerPort: 8200
        env:
        - name: NODE_TYPE
          value: "training"
        - name: GATEWAY_URL
          value: "http://gateway:8001"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "8"
```

## ConfigMap and Secrets

```yaml
# k8s/config/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: solanalm-config
  namespace: solanalm
data:
  SOLANA_NETWORK: "devnet"
  GATEWAY_HOST: "0.0.0.0"
  GATEWAY_PORT: "8001"
  LOG_LEVEL: "INFO"
---
# k8s/config/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: solanalm-secrets
  namespace: solanalm
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/solanalm"
  REDIS_URL: "redis://redis:6379"
  WALLET_ADDRESS: "YourWalletAddress"
  JWT_SECRET: "your-jwt-secret"
  OPENAI_API_KEY: "sk-..."
```

## Ingress Configuration

```yaml
# k8s/ingress/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: solanalm-ingress
  namespace: solanalm
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.solanalm.io
    secretName: solanalm-tls
  rules:
  - host: api.solanalm.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway
            port:
              number: 8001
```

## Horizontal Pod Autoscaler

```yaml
# k8s/autoscaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
  namespace: solanalm
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-hpa
  namespace: solanalm
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-node
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
```

## Persistent Volume Claims

```yaml
# k8s/storage/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
  namespace: solanalm
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs
  resources:
    requests:
      storage: 100Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: solanalm
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ssd
  resources:
    requests:
      storage: 50Gi
```

## Database Deployment

```yaml
# k8s/database/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: solanalm
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: solanalm
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: solanalm-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          value: solanalm
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: solanalm
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
  clusterIP: None
```

## GPU Scheduling

```yaml
# k8s/gpu/gpu-node-selector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-gpu
  namespace: solanalm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: inference-gpu
  template:
    spec:
      nodeSelector:
        accelerator: nvidia-tesla-v100
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: inference
        resources:
          limits:
            nvidia.com/gpu: 1
```

## Monitoring Stack

```yaml
# k8s/monitoring/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: solanalm-monitor
  namespace: solanalm
spec:
  selector:
    matchLabels:
      app: gateway
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

## Helm Chart (Optional)

```yaml
# helm/solanalm/values.yaml
replicaCount:
  gateway: 2
  inference: 3
  training: 2

image:
  repository: solanalm
  pullPolicy: IfNotPresent
  tag: "latest"

solana:
  network: devnet
  rpcUrl: https://api.devnet.solana.com

resources:
  gateway:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

  inference:
    requests:
      memory: "2Gi"
      cpu: "1"
      nvidia.com/gpu: 1
    limits:
      memory: "8Gi"
      cpu: "4"
      nvidia.com/gpu: 1

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilization: 70

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.solanalm.io
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: solanalm-tls
      hosts:
        - api.solanalm.io

postgresql:
  enabled: true
  auth:
    database: solanalm

redis:
  enabled: true
  architecture: standalone
```

```bash
# Install with Helm
helm install solanalm ./helm/solanalm -n solanalm --create-namespace -f values.yaml
```

## Deployment Commands

```bash
# Apply all manifests
kubectl apply -k k8s/

# Check status
kubectl get all -n solanalm

# View logs
kubectl logs -f deployment/gateway -n solanalm

# Scale deployment
kubectl scale deployment inference-node --replicas=5 -n solanalm

# Rolling update
kubectl set image deployment/gateway gateway=solanalm/gateway:v2 -n solanalm

# Rollback
kubectl rollout undo deployment/gateway -n solanalm
```

## Troubleshooting

### Pod Issues

```bash
# Check pod status
kubectl describe pod <pod-name> -n solanalm

# View logs
kubectl logs <pod-name> -n solanalm --previous

# Exec into pod
kubectl exec -it <pod-name> -n solanalm -- /bin/bash
```

### Network Issues

```bash
# Test service connectivity
kubectl run -it --rm debug --image=busybox -n solanalm -- wget -qO- http://gateway:8001/health

# Check endpoints
kubectl get endpoints -n solanalm
```

## Next Steps

- [Production Guide](production.md) - Production best practices
- [Docker Deployment](docker.md) - Container basics
