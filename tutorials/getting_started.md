# 🚀 Getting Started with SolanaLM

Welcome to SolanaLM - the first decentralized AI network with Tor-like privacy and federated learning capabilities!

## 📋 Quick Setup

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/solanalm.git
cd solanalm

# Install dependencies
pip install -r requirements.txt

# Install client SDK
pip install -e client/python/
```

### 2. Start the Network

```bash
# Terminal 1: Start the gateway
python scripts/run_gateway.py --enable-privacy

# Terminal 2: Start an inference node
python scripts/run_node.py --type inference --privacy-enabled

# Terminal 3: Start a training node
python scripts/run_node.py --type training --gpu-enabled
```

### 3. Your First Request

```python
from client.python.solanalm_client import SolanaLMClient

async with SolanaLMClient() as client:
    response = await client.inference(
        model="gpt-3.5-turbo",
        prompt="Hello, SolanaLM!",
        wallet_address="your-solana-wallet"
    )
    print(response.response)
```

## 🕵️ Privacy Features

### Basic Private Inference

```python
# Standard privacy (3 hops, basic anonymity)
response = await client.private_inference(
    model="gpt-4",
    prompt="Sensitive business question",
    privacy_level="standard",
    wallet_address="your-wallet"
)
```

### High Privacy Mode

```python
# High privacy (4-5 hops, geographic diversity)
response = await client.private_inference(
    model="gpt-4",
    prompt="Confidential research query",
    privacy_level="high",
    wallet_address="your-wallet"
)
```

### Maximum Privacy Mode

```python
# Maximum privacy (5+ hops, payment mixing)
response = await client.private_inference(
    model="gpt-4",
    prompt="Whistleblowing investigation",
    privacy_level="maximum",
    wallet_address="your-wallet"
)
```

## 🔄 OpenAI Compatibility

### Drop-in Replacement

```python
import openai

# Just change the API base URL
openai.api_key = "your-solana-wallet"
openai.api_base = "http://localhost:8001/v1"

# Use exactly like OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### With Privacy Headers

```python
# Add privacy to any OpenAI call
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Private query"}],
    headers={"X-Privacy-Level": "high"}
)
```

## 🤝 Federated Learning

### Join Training Rounds

```python
# Participate in federated learning
training_config = await client.join_training_round(
    model_name="llama-7b",
    node_capabilities={
        "gpu_memory": 24,
        "compute_power": "high"
    },
    reward_expectation=0.05  # SOL per round
)
```

### Monitor Your Rewards

```python
# Check training earnings
status = await client.get_training_status()
print(f"Total rewards: {status['total_rewards']} SOL")
print(f"Active rounds: {status['active_rounds']}")
```

## 💰 Cost Optimization

### Model Selection by Cost

```python
# Choose model based on budget
models_by_cost = [
    "gpt-3.5-turbo",  # Lowest cost
    "claude-3",       # Medium cost
    "gpt-4"          # Highest cost, best quality
]

for model in models_by_cost:
    try:
        response = await client.inference(
            model=model,
            prompt="Your question",
            wallet_address="your-wallet"
        )
        print(f"{model}: {response.cost_sol} SOL")
        break  # Use first available model
    except:
        continue
```

### Batch Processing for Savings

```python
# Process multiple prompts efficiently
prompts = [
    "Question 1",
    "Question 2",
    "Question 3"
]

# Batch saves ~20-30% on costs
responses = await client.batch_inference(
    model="gpt-3.5-turbo",
    prompts=prompts,
    wallet_address="your-wallet"
)
```

## 🛡️ Error Handling

### Automatic Retries

```python
async def resilient_inference(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.inference(
                model="gpt-4",
                prompt=prompt,
                wallet_address="your-wallet",
                timeout=30
            )
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### Model Fallbacks

```python
# Try multiple models
preferred_models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]

for model in preferred_models:
    try:
        response = await client.inference(
            model=model,
            prompt="Your question",
            wallet_address="your-wallet"
        )
        break
    except:
        continue
```

## 📊 Monitoring & Analytics

### Usage Analytics

```python
# Track your usage and costs
analytics = await client.get_usage_analytics(
    wallet_address="your-wallet",
    period="last_7_days"
)

print(f"Total requests: {analytics['total_requests']}")
print(f"Total cost: {analytics['total_cost']} SOL")
print(f"Privacy usage: {analytics['privacy_percentage']}%")
```

### Network Health

```python
# Monitor network performance
health = await client.get_network_health()
print(f"Active nodes: {health['active_nodes']}")
print(f"Success rate: {health['success_rate']}%")
```

## 🎯 Common Use Cases

### 1. **Business Intelligence**

```python
# Private competitive research
response = await client.private_inference(
    model="gpt-4",
    prompt="Analyze market trends in competitor space",
    privacy_level="high",
    wallet_address="your-wallet"
)
```

### 2. **Personal Sensitive Queries**

```python
# Health, legal, financial questions
response = await client.private_inference(
    model="gpt-4",
    prompt="Medical symptoms and treatment options",
    privacy_level="maximum",
    wallet_address="your-wallet"
)
```

### 3. **Research & Development**

```python
# Explore ideas without revealing research direction
response = await client.private_inference(
    model="gpt-4",
    prompt="Novel approaches to quantum computing",
    privacy_level="high",
    wallet_address="your-wallet"
)
```

### 4. **Content Generation**

```python
# Batch content generation
prompts = [
    "Write a blog post about AI ethics",
    "Create marketing copy for a new product",
    "Generate social media content ideas"
]

responses = await client.batch_inference(
    model="gpt-3.5-turbo",
    prompts=prompts,
    wallet_address="your-wallet"
)
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional configuration
export SOLANALM_GATEWAY_URL="http://localhost:8001"
export SOLANALM_DEFAULT_MODEL="gpt-3.5-turbo"
export SOLANALM_DEFAULT_PRIVACY="standard"
export SOLANALM_WALLET_ADDRESS="your-wallet"
```

### Client Configuration

```python
client = SolanaLMClient(
    gateway_url="http://localhost:8001",
    default_model="gpt-3.5-turbo",
    default_privacy_level="standard",
    default_wallet="your-wallet",
    timeout=60,
    max_retries=3
)
```

## 📈 Performance Tips

### 1. **Use Appropriate Privacy Levels**
- **Standard**: General queries, basic privacy needs
- **High**: Business intelligence, competitive research
- **Maximum**: Whistleblowing, investigative journalism

### 2. **Optimize Model Selection**
- **gpt-3.5-turbo**: Fast, cost-effective for most tasks
- **gpt-4**: Higher quality, more expensive
- **claude-3**: Good balance of quality and cost

### 3. **Batch When Possible**
- Group similar requests together
- Save 20-30% on costs
- Reduce network overhead

### 4. **Monitor Your Usage**
- Track costs with analytics
- Set up usage alerts
- Optimize based on patterns

## 🚨 Best Practices

### Security
- Never share your wallet private key
- Use environment variables for sensitive config
- Monitor for unusual usage patterns

### Privacy
- Choose appropriate privacy levels for your use case
- Understand the latency vs privacy trade-offs
- Use maximum privacy for truly sensitive queries

### Cost Management
- Start with lower-cost models
- Use batch processing for multiple requests
- Monitor analytics to optimize spending

### Performance
- Implement retry logic with exponential backoff
- Use model fallbacks for reliability
- Cache responses when appropriate

## 🎯 Next Steps

1. **Try the Examples**
   ```bash
   python examples/basic_usage.py
   python examples/privacy_demo.py
   python client/python/advanced_examples.py
   ```

2. **Run the Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Deploy Your Own Node**
   ```bash
   python scripts/run_node.py --type inference --privacy-enabled
   ```

4. **Join the Community**
   - Read the [Privacy Documentation](docs/tor_like_privacy.md)
   - Check out [Architecture Overview](docs/architecture.md)
   - Contribute to the [GitHub Repository](https://github.com/yourusername/solanalm)

## 🆘 Getting Help

### Common Issues

**Q: "Connection refused" error**
```bash
# Make sure the gateway is running
python scripts/run_gateway.py --enable-privacy
```

**Q: "Insufficient SOL balance" error**
```bash
# Fund your Solana wallet with SOL for payments
# Use devnet/testnet for development
```

**Q: "No nodes available" error**
```bash
# Start at least one inference node
python scripts/run_node.py --type inference
```

### Documentation
- [API Reference](docs/api_reference.md)
- [Privacy Guide](docs/tor_like_privacy.md)
- [Architecture](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

### Support
- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive guides and examples
- Community: Join discussions and get help

---

**🎉 Welcome to the future of private, decentralized AI!**

Start building privacy-preserving AI applications today with SolanaLM's unique combination of Tor-like anonymity, federated learning, and blockchain payments.