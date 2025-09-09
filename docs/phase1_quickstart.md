# SolanaLM Phase 1 Quick Start Guide

## Overview

This guide provides step-by-step instructions for getting started with SolanaLM Phase 1, focusing on the three critical components for technical adoption: dataset management, model storage, and inference deployment.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 22.04 (recommended)
- **GPU**: NVIDIA GPU with 16GB+ VRAM (RTX 4060 Ti minimum)
- **RAM**: 32GB+ system memory
- **Storage**: 100GB+ free disk space
- **Network**: 100Mbps+ upload speed

### Software Requirements
- Python 3.10+
- CUDA 12.1+
- Solana CLI tools
- Arweave wallet

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/solanalm.git
cd solanalm
```

### 2. Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Solana Tools
```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
```

### 4. Set Up Arweave Wallet
```bash
# Create or import your Arweave wallet
# Save wallet JSON to ~/.arweave/wallet.json
mkdir -p ~/.arweave
```

## Component Setup

### 1. Dataset Management

#### Using Public Datasets
```python
# Example: Using WikiText dataset
from core.trainer.datasets import WikiTextProvider

# Initialize provider
config = {"dataset_path": "./data/wikitext"}
provider = WikiTextProvider(config)

# Get training batch
batch = provider.get_training_batch(batch_size=32)
```

#### Creating Synthetic Data
```python
# Example: Generating synthetic code data
from core.trainer.datasets import SyntheticDataProvider

# Initialize provider for code generation
config = {
    "type": "code",
    "language": "python",
    "complexity": "intermediate"
}
provider = SyntheticDataProvider(config)

# Generate training data
batch = provider.get_training_batch(batch_size=32)
```

### 2. Model Storage

#### Uploading a Model
```python
# Example: Uploading a trained model
from core.storage.arweave import ArweaveStorage
from core.storage.registry import ModelRegistry

# Initialize storage
storage = ArweaveStorage("~/.arweave/wallet.json")
registry = ModelRegistry(SOLANA_RPC_URL, SOLANA_WALLET)

# Save model locally first
model.save_weights("./model_weights.pth")

# Upload to Arweave
metadata = {
    "name": "code-model-v1",
    "version": "1.0.0",
    "architecture": "qwen-slm-1.8b",
    "domain": "code"
}
tx_id = storage.upload_model("./model_weights.pth", metadata)

# Register on Solana
registry.register_model("code-model-v1", "1.0.0", tx_id)
```

#### Downloading a Model
```python
# Example: Downloading a model for inference
from core.storage.interface import ModelStorageInterface

# Initialize storage interface
storage = ModelStorageInterface("~/.arweave/wallet.json", SOLANA_PROGRAM_ID)

# Load model for inference
model = storage.get_model_for_inference("code-model-v1")
```

### 3. Inference Gateway

#### Starting the Server
```bash
# Start the inference server
cd core/inference
python server.py --host 0.0.0.0 --port 8000
```

#### Using the OpenAI-Compatible API
```python
# Example: Using the API with OpenAI SDK
import openai

# Configure client
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "your-api-key"  # Solana wallet address

# Make a chat completion request
response = openai.ChatCompletion.create(
    model="code-model-v1",
    messages=[
        {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
    ],
    temperature=0.7,
    max_tokens=200
)

print(response.choices[0].message.content)
```

#### Using with LangChain
```python
# Example: Integration with LangChain
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Configure LLM
llm = OpenAI(
    model_name="code-model-v1",
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="your-api-key"
)

# Create chain
template = "Write a {language} function to {task}"
prompt = PromptTemplate.from_template(template)
chain = LLMChain(llm=llm, prompt=prompt)

# Run chain
result = chain.run(language="Python", task="calculate fibonacci numbers")
print(result)
```

## Training Workflow

### 1. Set Up Trainer Node
```bash
# Start trainer node
cd core/trainer
python node.py --config config/trainer.yaml
```

### 2. Register for Training Job
```python
# Example: Registering for a training job
from core.trainer.coordinator import SolanaInterface

# Initialize Solana interface
solana = SolanaInterface(SOLANA_RPC_URL, SOLANA_WALLET)

# Register for job
job_id = "job_12345"
solana.register_for_job(job_id)
```

### 3. Participate in Training Round
```python
# Example: Participating in a training round
from core.trainer.node import TrainerNode

# Initialize trainer node
config = {
    "batch_size": 32,
    "learning_rate": 1e-4,
    "data_provider": "wikitext"
}
node = TrainerNode(config, SOLANA_RPC_URL)

# Participate in round
round_id = 1
node.participate_in_round(job_id, round_id)
```

## Testing and Validation

### Running Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific component tests
pytest tests/unit/test_storage.py
pytest tests/unit/test_inference.py
```

### Running Integration Tests
```bash
# Run integration tests
pytest tests/integration/test_end_to_end.py
```

### Performance Benchmarking
```bash
# Run performance benchmarks
python benchmarks/run_benchmarks.py
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```
   Solution: Reduce batch size in configuration
   ```

2. **Solana RPC Connection Failed**
   ```
   Solution: Check RPC endpoint and network connectivity
   ```

3. **Arweave Upload Failed**
   ```
   Solution: Check wallet balance and network status
   ```

4. **Model Loading Slow**
   ```
   Solution: Check network bandwidth and storage performance
   ```

### Getting Help

- **Documentation**: Check docs/ directory
- **Community**: Join our Discord server
- **Issues**: File GitHub issues for bugs
- **Support**: Contact team@solanalm.ai for direct support

## Next Steps

1. **Complete the Tutorials**: Work through the example implementations
2. **Join the Beta**: Register for access to the testnet
3. **Build Your Model**: Fine-tune models for your specific use cases
4. **Contribute**: Help improve the platform by contributing code

## Resources

- **API Documentation**: docs/api_reference.md
- **Architecture Guide**: docs/architecture.md
- **Deployment Guide**: docs/deployment_guide.md
- **Example Projects**: examples/

This quick start guide provides everything needed to begin working with SolanaLM Phase 1. The modular design allows you to focus on the components most relevant to your use case while maintaining compatibility with the entire ecosystem.