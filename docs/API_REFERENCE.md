# SolanaLM API Reference

## Table of Contents
- [Gateway API](#gateway-api)
- [Node Management API](#node-management-api)
- [Federated Learning API](#federated-learning-api)
- [Monitoring API](#monitoring-api)
- [Authentication API](#authentication-api)
- [Client SDKs](#client-sdks)

## Gateway API

### Base URL
```
http://localhost:8001
```

### OpenAI Compatible Endpoints

#### POST /v1/chat/completions
OpenAI-compatible chat completions endpoint.

**Request Body:**
```json
{
  "model": "string",
  "messages": [
    {
      "role": "user",
      "content": "string"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "wallet_address": "string"
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "model-name",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  },
  "cost_sol": 0.001,
  "node_id": "node-123"
}
```

### SolanaLM Specific Endpoints

#### POST /inference
Direct inference endpoint with extended features.

**Request Body:**
```json
{
  "prompt": "string",
  "model": "string",
  "max_tokens": 150,
  "temperature": 0.7,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "wallet_address": "string",
  "privacy_level": "standard",
  "preferred_node": "optional-node-id"
}
```

**Response:**
```json
{
  "response": "Generated text response",
  "model": "model-name",
  "tokens_generated": 42,
  "processing_time": 1.23,
  "node_id": "node-123",
  "request_id": "req-abc123",
  "cost_sol": 0.001,
  "privacy_circuit": ["node1", "node2", "node3"]
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "gateway": "healthy",
    "registry": "healthy",
    "payment_client": "healthy",
    "database": "healthy"
  },
  "network": {
    "total_nodes": 15,
    "active_nodes": 12,
    "total_requests": 1542,
    "avg_response_time": 0.85
  }
}
```

## Node Management API

### POST /nodes/register
Register a new node with the network.

**Request Body:**
```json
{
  "node_id": "string",
  "node_type": "inference|training|proxy|hybrid",
  "wallet_address": "string",
  "endpoint": "http://node-url:port",
  "capabilities": {
    "supported_models": ["model1", "model2"],
    "max_concurrent_requests": 10,
    "gpu_memory_gb": 8,
    "cpu_cores": 4,
    "storage_gb": 100
  },
  "pricing": {
    "cost_per_token": 0.000001,
    "cost_per_training_sample": 0.00001
  }
}
```

**Response:**
```json
{
  "status": "registered",
  "node_id": "string",
  "registration_time": "2024-01-01T12:00:00Z",
  "initial_reputation": 1.0
}
```

### GET /nodes
List all registered nodes.

**Query Parameters:**
- `node_type`: Filter by node type
- `status`: Filter by status (active, inactive, maintenance)
- `model`: Filter by supported model

**Response:**
```json
{
  "nodes": [
    {
      "node_id": "node-123",
      "node_type": "inference",
      "wallet_address": "wallet-address",
      "endpoint": "http://node-url:port",
      "status": "active",
      "reputation_score": 0.95,
      "last_seen": "2024-01-01T12:00:00Z",
      "capabilities": {
        "supported_models": ["model1", "model2"],
        "max_concurrent_requests": 10
      },
      "statistics": {
        "total_requests": 1000,
        "successful_requests": 995,
        "avg_response_time": 0.85,
        "uptime_percentage": 99.5
      }
    }
  ],
  "total": 15,
  "active": 12
}
```

## Federated Learning API

### POST /training/start-round
Start a new federated learning round.

**Request Body:**
```json
{
  "model_name": "string",
  "algorithm": "fedavg|fedprox|fedadam|scaffold",
  "participating_nodes": ["node1", "node2", "node3"],
  "round_config": {
    "local_epochs": 3,
    "learning_rate": 0.01,
    "batch_size": 32,
    "aggregation_strategy": "weighted_average"
  },
  "privacy_settings": {
    "differential_privacy": true,
    "noise_level": 0.1,
    "secure_aggregation": true
  }
}
```

**Response:**
```json
{
  "round_id": "round-123",
  "status": "started",
  "participating_nodes": ["node1", "node2", "node3"],
  "estimated_completion": "2024-01-01T12:30:00Z"
}
```

### GET /training/rounds/{round_id}
Get status of a specific training round.

**Response:**
```json
{
  "round_id": "round-123",
  "status": "completed",
  "algorithm": "fedavg",
  "participating_nodes": ["node1", "node2", "node3"],
  "start_time": "2024-01-01T12:00:00Z",
  "completion_time": "2024-01-01T12:25:00Z",
  "results": {
    "global_loss": 0.1234,
    "global_accuracy": 0.8765,
    "convergence_metrics": {
      "loss_improvement": 0.0123,
      "gradient_norm": 0.456,
      "model_variance": 0.0789
    },
    "communication_cost": 1000000,
    "computation_time": 1500.0
  },
  "node_contributions": {
    "node1": {
      "local_loss": 0.1200,
      "data_samples": 1000,
      "computation_time": 500.0
    }
  }
}
```

## Monitoring API

### GET /metrics
Get comprehensive system metrics.

**Response:**
```json
{
  "network": {
    "total_nodes": 15,
    "active_nodes": 12,
    "total_requests": 10000,
    "successful_requests": 9950,
    "total_tokens_generated": 1000000,
    "avg_response_time": 0.85,
    "requests_per_second": 5.2
  },
  "training": {
    "active_rounds": 2,
    "completed_rounds": 50,
    "total_participants": 100,
    "avg_round_time": 1800.0
  },
  "payments": {
    "total_transactions": 5000,
    "total_volume_sol": 10.5,
    "avg_cost_per_request": 0.001
  },
  "performance": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "network_io": {
      "bytes_sent": 1000000,
      "bytes_received": 2000000
    }
  }
}
```

### GET /metrics/prometheus
Get metrics in Prometheus format for monitoring systems.

**Response:** (Prometheus text format)
```
# HELP solanalm_total_requests Total number of inference requests
# TYPE solanalm_total_requests counter
solanalm_total_requests{node_type="inference"} 1000

# HELP solanalm_response_time_seconds Response time in seconds
# TYPE solanalm_response_time_seconds histogram
solanalm_response_time_seconds_bucket{le="0.1"} 100
solanalm_response_time_seconds_bucket{le="0.5"} 450
solanalm_response_time_seconds_bucket{le="1.0"} 800
```

## Authentication API

### POST /auth/login
Authenticate user and get JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "user-123",
    "username": "string",
    "role": "admin|node_operator|client|readonly"
  }
}
```

### POST /auth/wallet-login
Authenticate using Solana wallet signature.

**Request Body:**
```json
{
  "wallet_address": "string",
  "message": "string",
  "signature": "string"
}
```

### POST /auth/api-keys
Create a new API key.

**Request Body:**
```json
{
  "name": "string",
  "permissions": ["inference", "training", "monitoring"],
  "rate_limit": 1000,
  "expires_in_days": 365
}
```

**Response:**
```json
{
  "api_key": "sk-1234567890abcdef",
  "key_id": "key-123",
  "name": "string",
  "created_at": "2024-01-01T12:00:00Z",
  "expires_at": "2025-01-01T12:00:00Z"
}
```

## Client SDKs

### Python SDK

#### Installation
```bash
pip install solanalm-client
```

#### Basic Usage
```python
import asyncio
from solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:
        # Standard inference
        response = await client.inference(
            model="microsoft/DialoGPT-small",
            prompt="Hello, world!",
            wallet_address="your-wallet-address"
        )
        print(response.response)

        # Private inference
        response = await client.private_inference(
            model="microsoft/DialoGPT-small",
            prompt="Sensitive query",
            wallet_address="your-wallet-address",
            circuit_length=3
        )

        # Training participation
        await client.join_training_round(
            model_name="custom-model",
            training_data=your_data,
            wallet_address="your-wallet-address"
        )

asyncio.run(main())
```

#### OpenAI Compatibility
```python
from solanalm_client import OpenAICompatibleClient

client = OpenAICompatibleClient(
    base_url="http://localhost:8001/v1",
    api_key="your-solana-wallet-address"
)

response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

## Error Codes

### HTTP Status Codes
- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Custom Error Codes
```json
{
  "error": {
    "code": "INSUFFICIENT_NODES",
    "message": "Not enough active nodes to process request",
    "details": {
      "required_nodes": 1,
      "available_nodes": 0,
      "suggested_action": "Try again later or register more nodes"
    }
  }
}
```

Common error codes:
- `INSUFFICIENT_NODES` - Not enough nodes available
- `MODEL_NOT_SUPPORTED` - Requested model not supported by any node
- `WALLET_INVALID` - Invalid Solana wallet address
- `PAYMENT_FAILED` - Payment processing failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `NODE_UNAVAILABLE` - Specific node is unavailable
- `TRAINING_ROUND_FULL` - Training round has maximum participants

## Rate Limits

Default rate limits:
- **Public endpoints**: 100 requests per minute per IP
- **Authenticated users**: 1000 requests per hour
- **API keys**: Configurable per key (default 1000/hour)
- **Node operators**: 10000 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Configuration
Register webhook URLs to receive real-time notifications:

```json
{
  "webhook_url": "https://your-app.com/webhooks/solanalm",
  "events": ["inference.completed", "training.round_completed", "node.status_changed"],
  "secret": "webhook-secret-for-verification"
}
```

### Event Types
- `inference.completed` - Inference request completed
- `inference.failed` - Inference request failed
- `training.round_started` - New training round started
- `training.round_completed` - Training round completed
- `node.registered` - New node registered
- `node.status_changed` - Node status changed
- `payment.completed` - Payment processed
- `system.alert` - System alert or warning

### Webhook Payload
```json
{
  "event": "inference.completed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "request_id": "req-123",
    "node_id": "node-456",
    "model": "microsoft/DialoGPT-small",
    "tokens_generated": 42,
    "processing_time": 1.23,
    "cost_sol": 0.001
  }
}
```