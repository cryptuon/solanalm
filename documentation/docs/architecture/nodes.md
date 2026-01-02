# Node Types

SolanaLM supports multiple node types, each serving different purposes in the network.

## Node Types Overview

| Type | Purpose | Earnings | Requirements |
|------|---------|----------|--------------|
| **Inference** | Process LLM requests | Per-request fees | GPU, models |
| **Training** | Federated learning | Training rewards | Compute, data |
| **Proxy** | Route to external APIs | Commission | API keys |
| **Hybrid** | Both inference + training | Dual revenue | All above |

## Inference Nodes

Process LLM inference requests using local models.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                 Inference Node                    │
│  ┌────────────────────────────────────────────┐  │
│  │              HTTP Server                    │  │
│  │         (FastAPI / Uvicorn)                 │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │            Request Handler                  │  │
│  │  • Authentication    • Validation           │  │
│  │  • Rate limiting     • Request queuing      │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │            Model Manager                    │  │
│  │  • Model loading     • Memory management    │  │
│  │  • Batch processing  • Caching              │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │         PyTorch / Transformers              │  │
│  │              Model Runtime                  │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Implementation

```python
# core/nodes/inference/node.py
class InferenceNode:
    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        model_name: str,
        port: int = 8100
    ):
        self.node_id = node_id
        self.wallet_address = wallet_address
        self.gateway_url = gateway_url
        self.model_name = model_name
        self.port = port
        self.model = None
        self.tokenizer = None

    async def initialize(self):
        """Load model and register with gateway"""
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        # Register with gateway
        await self.register()

    async def process_request(self, request: InferenceRequest):
        """Process an inference request"""
        inputs = self.tokenizer(
            request.prompt,
            return_tensors="pt"
        )

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )

        response = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        return InferenceResponse(
            response=response,
            tokens_generated=len(outputs[0])
        )
```

### Supported Backends

| Backend | Models | Performance |
|---------|--------|-------------|
| **Transformers** | Hugging Face models | Good |
| **llama.cpp** | GGML models | Fast on CPU |
| **vLLM** | Large models | Best GPU |
| **TensorRT** | Optimized models | Fastest |

## Training Nodes

Participate in federated learning rounds.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                 Training Node                     │
│  ┌────────────────────────────────────────────┐  │
│  │           Training Controller               │  │
│  │  • Round management   • State machine       │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │            Data Manager                     │  │
│  │  • Local dataset     • Preprocessing        │  │
│  │  • Augmentation      • Batching             │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │            Training Engine                  │  │
│  │  • Local training    • Gradient computation │  │
│  │  • DP noise          • Model updates        │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │         Secure Aggregation Client          │  │
│  │  • Update encryption • Mask generation     │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Training Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    IDLE     │────▶│  SELECTED   │────▶│  DOWNLOAD   │
│             │     │             │     │   MODEL     │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ▲                                       │
       │                                       ▼
┌──────┴──────┐     ┌─────────────┐     ┌─────────────┐
│   REWARD    │◀────│   UPLOAD    │◀────│  TRAINING   │
│   RECEIVED  │     │   UPDATE    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Implementation

```python
# core/nodes/training/node.py
class TrainingNode:
    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        local_epochs: int = 5,
        learning_rate: float = 0.01
    ):
        self.node_id = node_id
        self.local_epochs = local_epochs
        self.learning_rate = learning_rate

    async def train_round(self, global_model, round_config):
        """Execute a local training round"""
        # Download global model
        model = self.load_model(global_model)

        # Local training
        optimizer = torch.optim.SGD(
            model.parameters(),
            lr=self.learning_rate
        )

        for epoch in range(self.local_epochs):
            for batch in self.data_loader:
                loss = self.compute_loss(model, batch)
                loss.backward()

                # Add DP noise if enabled
                if self.differential_privacy:
                    self.add_noise(model)

                optimizer.step()
                optimizer.zero_grad()

        # Compute update
        update = self.compute_update(global_model, model)

        return update
```

## Proxy Nodes

Route requests to external API providers.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  Proxy Node                       │
│  ┌────────────────────────────────────────────┐  │
│  │            Request Router                   │  │
│  │  • Provider selection • Model mapping       │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │            Provider Clients                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │  │
│  │  │ OpenAI  │ │Anthropic│ │ Cohere  │       │  │
│  │  │ Client  │ │ Client  │ │ Client  │       │  │
│  │  └─────────┘ └─────────┘ └─────────┘       │  │
│  └─────────────────────┬──────────────────────┘  │
│                        │                          │
│  ┌─────────────────────▼──────────────────────┐  │
│  │           Rate Limiter / Cache              │  │
│  │  • Request throttling • Response caching    │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Implementation

```python
# core/nodes/proxy/node.py
class ProxyNode:
    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        openai_api_key: str = None,
        anthropic_api_key: str = None
    ):
        self.node_id = node_id
        self.providers = {}

        if openai_api_key:
            self.providers['openai'] = OpenAIProvider(openai_api_key)
        if anthropic_api_key:
            self.providers['anthropic'] = AnthropicProvider(anthropic_api_key)

    async def process_request(self, request):
        """Route request to appropriate provider"""
        provider = self.select_provider(request.model)

        # Forward request
        response = await provider.complete(
            model=request.model,
            prompt=request.prompt,
            **request.params
        )

        # Add commission
        cost = response.cost * (1 + self.commission_rate)

        return ProxyResponse(
            response=response.text,
            cost=cost,
            provider=provider.name
        )
```

### Supported Providers

| Provider | Models | Features |
|----------|--------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | Chat, completions |
| **Anthropic** | Claude 3, Claude 2 | Chat, analysis |
| **Cohere** | Command, Embed | Chat, embeddings |
| **Ollama** | Local models | Self-hosted |

## Hybrid Nodes

Combine inference and training capabilities.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  Hybrid Node                      │
│  ┌────────────────────────────────────────────┐  │
│  │              Mode Controller                │  │
│  │  • Mode switching    • Resource allocation  │  │
│  └────────────────────────┬───────────────────┘  │
│                           │                       │
│         ┌─────────────────┼─────────────────┐    │
│         │                 │                 │    │
│  ┌──────▼──────┐   ┌──────▼──────┐         │    │
│  │  Inference  │   │  Training   │         │    │
│  │   Module    │   │   Module    │         │    │
│  └─────────────┘   └─────────────┘         │    │
│                                             │    │
│  ┌──────────────────────────────────────────┘    │
│  │         Shared Resources                      │
│  │  • GPU memory        • Model storage         │
│  │  • Network bandwidth • Local data            │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Mode Switching

```python
class HybridNode:
    def __init__(self, ...):
        self.mode = NodeMode.INFERENCE
        self.inference_module = InferenceNode(...)
        self.training_module = TrainingNode(...)

    async def switch_mode(self, new_mode: NodeMode):
        """Switch between inference and training modes"""
        if self.mode == new_mode:
            return

        if new_mode == NodeMode.TRAINING:
            # Pause inference
            await self.inference_module.pause()
            # Start training
            await self.training_module.activate()
        else:
            # Pause training
            await self.training_module.pause()
            # Resume inference
            await self.inference_module.resume()

        self.mode = new_mode
```

## Node Lifecycle

### Registration

```python
async def register(self):
    """Register node with gateway"""
    registration = NodeRegistration(
        node_id=self.node_id,
        wallet_address=self.wallet_address,
        node_type=self.node_type,
        capabilities=self.get_capabilities(),
        supported_models=self.get_models(),
        endpoint=f"http://{self.host}:{self.port}"
    )

    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{self.gateway_url}/nodes/register",
            json=registration.dict()
        )
```

### Health Reporting

```python
async def health_check_loop(self):
    """Periodic health reporting"""
    while self.running:
        health = NodeHealth(
            node_id=self.node_id,
            status="healthy",
            current_load=self.get_load(),
            memory_usage=self.get_memory(),
            requests_processed=self.request_count
        )

        await self.report_health(health)
        await asyncio.sleep(30)
```

### Graceful Shutdown

```python
async def shutdown(self):
    """Graceful shutdown"""
    self.running = False

    # Complete pending requests
    await self.complete_pending()

    # Deregister from gateway
    await self.deregister()

    # Cleanup resources
    await self.cleanup()
```

## Resource Management

### GPU Memory

```python
def manage_gpu_memory(self):
    """Monitor and manage GPU memory"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()

        if allocated / reserved > 0.9:
            # Clear cache
            torch.cuda.empty_cache()
            gc.collect()
```

### Request Queuing

```python
class RequestQueue:
    def __init__(self, max_size=100):
        self.queue = asyncio.Queue(maxsize=max_size)

    async def enqueue(self, request):
        if self.queue.full():
            raise QueueFullError()
        await self.queue.put(request)

    async def process_loop(self):
        while True:
            request = await self.queue.get()
            await self.process(request)
            self.queue.task_done()
```

## Next Steps

- [Payment System](payments.md) - Blockchain integration
- [Architecture Overview](overview.md) - System design
- [Running Nodes](../guides/running-nodes.md) - Start your own node
