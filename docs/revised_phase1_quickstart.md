# SolanaLM Phase 1 Quick Start Guide (Revised)

## Overview

This guide provides step-by-step instructions for getting started with SolanaLM Phase 1, focusing on the three critical components for technical adoption: dataset management, decentralized model storage, and inference deployment.

**NOTE: This document has been revised to reflect a fully decentralized model storage approach, eliminating reliance on centralized storage providers like Arweave.**

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

#### Using Developer's Own Data
```python
# Example: Using your own data for fine-tuning
from core.trainer.datasets import DeveloperDataProvider

# Implement custom data provider
class MyCustomDataProvider(DeveloperDataProvider):
    def __init__(self, data_path, config):
        super().__init__(data_path, config)
        # Load your data
        self.data = self._load_my_data(data_path)
    
    def _load_my_data(self, data_path):
        # Implement your data loading logic
        pass
    
    def get_training_batch(self, batch_size):
        # Implement batch sampling from your data
        pass

# Register with trainer node
config = {"batch_size": 32, "epochs": 10}
provider = MyCustomDataProvider("/path/to/my/data", config)
trainer_node.register_data_provider(provider)
```

### 2. Decentralized Model Storage

#### Publishing a Model
```python
# Example: Publishing a trained model to the network
from core.storage.p2p import P2PModelStorage
from core.storage.registry import ModelRegistryInterface

# Initialize storage
storage = P2PModelStorage(SOLANA_RPC_URL)
registry = ModelRegistryInterface(SOLANA_PROGRAM_ID, SOLANA_WALLET)

# Save model locally first
model.save_weights("./model_weights.pth")

# Publish to network
metadata = {
    "name": "my-fine-tuned-model",
    "version": "1.0.0",
    "architecture": "qwen-slm-1.8b",
    "domain": "specialized-domain",
    "description": "Fine-tuned on my custom data"
}
model_id = storage.publish_model(model, metadata)
```

#### Downloading a Model
```python
# Example: Downloading a model for inference
from core.storage.interface import InferenceStorageInterface

# Initialize storage interface
storage = InferenceStorageInterface(SOLANA_PROGRAM_ID, SOLANA_RPC_URL)

# Load model for inference
model = storage.get_model_for_inference("model-id-from-network")
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
    model="my-fine-tuned-model",
    messages=[
        {"role": "user", "content": "Process my specialized data"}
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
    model_name="my-fine-tuned-model",
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="your-api-key"
)

# Create chain
template = "Process this {data_type} using my specialized model: {input_data}"
prompt = PromptTemplate.from_template(template)
chain = LLMChain(llm=llm, prompt=prompt)

# Run chain
result = chain.run(data_type="financial reports", input_data="Q3 earnings data")
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

### 3. Fine-tuning on Developer Data
```python
# Example: Fine-tuning a model on your own data
from core.trainer.node import TrainerNode

# Initialize trainer node
config = {
    "batch_size": 32,
    "learning_rate": 1e-4,
    "training_method": "lora"
}
node = TrainerNode(config, SOLANA_RPC_URL)

# Fine-tune on your data
fine_tuned_model_id = node.fine_tune_on_developer_data(
    base_model_id="qwen-code-slm-v1",
    developer_data_provider=my_custom_data_provider
)
```

### 4. Participate in Training Round
```python
# Example: Participating in a training round
from core.trainer.node import TrainerNode

# Initialize trainer node
config = {
    "batch_size": 32,
    "learning_rate": 1e-4,
    "data_provider": "my-custom-data"
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

3. **Model Download Slow**
   ```
   Solution: Check network bandwidth and peer availability
   ```

4. **Model Loading Slow**
   ```
   Solution: Check local storage performance
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
- **Developer Data Usage**: docs/developer_data_usage.md

This quick start guide provides everything needed to begin working with SolanaLM Phase 1. The modular design allows you to focus on the components most relevant to your use case while maintaining compatibility with the entire ecosystem. The revised decentralized approach to model storage eliminates dependencies on centralized providers while maintaining all the benefits of a distributed system.