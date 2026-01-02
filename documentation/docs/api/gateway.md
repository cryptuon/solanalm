# Gateway API Reference

The SolanaLM Gateway provides a REST API for all network operations.

## Base URL

```
http://localhost:8001
```

## Authentication

Requests require a Solana wallet address for payment authorization:

```bash
# As query parameter
curl "http://localhost:8001/inference?wallet_address=YOUR_WALLET"

# Or in request body
curl -X POST http://localhost:8001/inference \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "YOUR_WALLET", ...}'
```

## Endpoints

### Health & Status

#### GET /

Get gateway status and network statistics.

```bash
curl http://localhost:8001/
```

**Response:**

```json
{
  "service": "SolanaLM Gateway",
  "version": "1.0.0",
  "status": "running",
  "network_stats": {
    "total_nodes": 15,
    "active_nodes": 12,
    "inference_nodes": 8,
    "training_nodes": 3,
    "proxy_nodes": 1
  },
  "uptime": 3600
}
```

#### GET /health

Health check endpoint.

```bash
curl http://localhost:8001/health
```

**Response:**

```json
{
  "status": "healthy",
  "gateway": "running",
  "registry": "connected",
  "coordinator": "ready",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Inference

#### POST /inference

Submit an inference request.

**Request:**

```bash
curl -X POST http://localhost:8001/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model": "microsoft/DialoGPT-small",
    "prompt": "Hello, how are you?",
    "wallet_address": "YOUR_WALLET",
    "max_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9,
    "metadata": {}
  }'
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model identifier |
| `prompt` | string | Yes | Input prompt |
| `wallet_address` | string | Yes | Solana wallet for payment |
| `max_tokens` | integer | No | Maximum tokens (default: 100) |
| `temperature` | float | No | Sampling temperature (default: 0.7) |
| `top_p` | float | No | Nucleus sampling (default: 0.9) |
| `metadata` | object | No | Custom metadata |

**Response:**

```json
{
  "request_id": "req_abc123",
  "model": "microsoft/DialoGPT-small",
  "response": "I'm doing well, thank you for asking!",
  "processing_time": 0.234,
  "tokens_generated": 12,
  "cost_sol": 0.000012,
  "node_id": "inference-node-1"
}
```

#### POST /private_inference

Submit a privacy-preserving inference request using onion routing.

**Request:**

```bash
curl -X POST "http://localhost:8001/private_inference?privacy_level=standard" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "microsoft/DialoGPT-small",
    "prompt": "Sensitive query",
    "wallet_address": "YOUR_WALLET",
    "max_tokens": 100
  }'
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `privacy_level` | string | `standard` (3 hops) or `high` (5 hops) |

**Response:** Same as `/inference`

---

### Nodes

#### GET /nodes

List all registered nodes.

```bash
curl http://localhost:8001/nodes
```

**Response:**

```json
[
  {
    "node_id": "inference-node-1",
    "type": "inference",
    "status": "active",
    "wallet_address": "NodeWallet123",
    "supported_models": ["microsoft/DialoGPT-small", "gpt2"],
    "capabilities": {
      "gpu": true,
      "max_batch_size": 8
    },
    "metrics": {
      "requests_processed": 1500,
      "avg_latency": 0.234,
      "success_rate": 0.99
    }
  }
]
```

#### GET /nodes/{node_id}

Get specific node details.

```bash
curl http://localhost:8001/nodes/inference-node-1
```

---

### Training

#### GET /training/status

Get current federated learning status.

```bash
curl http://localhost:8001/training/status
```

**Response:**

```json
{
  "active_rounds": 1,
  "current_round": 42,
  "participating_nodes": 5,
  "global_loss": 0.234,
  "convergence_rate": 0.02,
  "next_round_start": "2024-01-15T11:00:00Z"
}
```

#### POST /training/join

Join a federated training round.

**Request:**

```bash
curl -X POST http://localhost:8001/training/join \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "custom-model",
    "node_capabilities": {
      "compute_power": "high",
      "data_samples": 1000,
      "gpu_available": true
    },
    "reward_expectation": 0.01
  }'
```

**Response:**

```json
{
  "status": "accepted",
  "round_id": "round_42",
  "model_download_url": "/training/models/custom-model/v42",
  "deadline": "2024-01-15T11:30:00Z",
  "expected_reward": 0.01
}
```

#### POST /training/custom

Start custom model training.

**Request:**

```bash
curl -X POST http://localhost:8001/training/custom \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "model_type": "transformer",
      "epochs": 10,
      "batch_size": 32,
      "learning_rate": 0.001
    },
    "wallet_address": "YOUR_WALLET"
  }'
```

---

### Privacy

#### GET /privacy_status

Get privacy network status.

```bash
curl http://localhost:8001/privacy_status
```

**Response:**

```json
{
  "privacy_capable_nodes": 10,
  "anonymity_set_size": 50,
  "circuit_diversity_score": 0.85,
  "geographic_coverage": 5,
  "avg_circuit_length": 3.2,
  "privacy_success_rate": 0.98
}
```

#### GET /privacy/circuit/{request_id}

Get circuit information for a private request.

```bash
curl http://localhost:8001/privacy/circuit/req_abc123
```

**Response:**

```json
{
  "request_id": "req_abc123",
  "hop_count": 3,
  "total_latency": 450,
  "circuit_id": "circuit_xyz",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Analytics

#### GET /analytics/usage

Get usage analytics for a wallet.

```bash
curl "http://localhost:8001/analytics/usage?wallet_address=YOUR_WALLET&period=last_7_days"
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `wallet_address` | string | Wallet to query |
| `period` | string | `last_7_days`, `last_30_days`, `all_time` |

**Response:**

```json
{
  "total_requests": 150,
  "total_cost": 0.015,
  "avg_latency": 0.234,
  "privacy_requests": 25,
  "privacy_percentage": 16.7,
  "top_model": "microsoft/DialoGPT-small"
}
```

---

### Metrics

#### GET /metrics

Get Prometheus-formatted metrics.

```bash
curl http://localhost:8001/metrics
```

**Response:**

```
# HELP solanalm_requests_total Total inference requests
# TYPE solanalm_requests_total counter
solanalm_requests_total{node_type="inference"} 1500

# HELP solanalm_response_time_seconds Response time histogram
# TYPE solanalm_response_time_seconds histogram
solanalm_response_time_seconds_bucket{le="0.1"} 500
solanalm_response_time_seconds_bucket{le="0.5"} 1200
solanalm_response_time_seconds_bucket{le="1.0"} 1450

# HELP solanalm_training_rounds_total Total training rounds
# TYPE solanalm_training_rounds_total counter
solanalm_training_rounds_total 42
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {}
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `unauthorized` | 401 | Invalid wallet/auth |
| `insufficient_funds` | 402 | Wallet has insufficient SOL |
| `not_found` | 404 | Resource not found |
| `rate_limited` | 429 | Too many requests |
| `no_nodes_available` | 503 | No nodes can serve request |
| `internal_error` | 500 | Server error |

---

## Rate Limiting

Default limits:

| Limit Type | Default | Notes |
|------------|---------|-------|
| Per minute | 100 | Per wallet |
| Per hour | 1000 | Per wallet |
| Burst | 20 | Concurrent requests |

Rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

---

## WebSocket API

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['node_status', 'training_updates']
}));
```

### Events

| Channel | Description |
|---------|-------------|
| `node_status` | Node online/offline events |
| `training_updates` | FL round progress |
| `network_metrics` | Real-time metrics |

## Next Steps

- [Client SDK Reference](client-sdk.md) - Python SDK details
- [OpenAI Compatibility](openai-compat.md) - OpenAI API compatibility
