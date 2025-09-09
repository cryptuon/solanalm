# Phase 1 Technical Specification: Complete System Integration

## Overview

This document specifies the complete technical implementation for Phase 1 of SolanaLM, integrating all core components to eliminate unknowns for technical adoption. The specification covers dataset management, model storage, inference gateway, and all integration points.

## System Architecture

### High-Level Components

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Trainer Node  │    │  Coordinator Node │    │ Inference Server │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Training       │    │  Solana Programs │    │  API Server      │
│  Framework      │◄──►│  (Solana)        │◄──►│  (FastAPI)       │
│  (PyTorch+FedML)│    │                  │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Dataset        │    │  Model Registry  │    │  Model Storage   │
│  Management     │    │  (Arweave+Solana)│    │  (Arweave)       │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## Core Components Specification

### 1. Solana Programs

#### Training Coordinator Program
```rust
// Program ID: TCoorD1nateR9tRainingJobsAndParticipants1111

// Accounts
#[account]
pub struct TrainingJob {
    pub id: Pubkey,
    pub model_spec: ModelSpec,
    pub data_req: DataReq,
    pub coordinator: Pubkey,
    pub escrow: Pubkey,
    pub status: JobStatus,
    pub current_round: u64,
    pub total_rounds: u64,
    pub reward_pool: u64,
}

#[account]
pub struct Participant {
    pub job_id: Pubkey,
    pub node: Pubkey,
    pub reputation: u64,
    pub stake: u64,
    pub last_participation: i64,
}

#[account]
pub struct Round {
    pub job_id: Pubkey,
    pub round_id: u64,
    pub participants: Vec<Pubkey>,
    pub submissions: u64,
    pub status: RoundStatus,
}

// Instructions
pub fn initialize_job(ctx: Context<InitializeJob>, spec: ModelSpec, data_req: DataReq, reward: u64) -> Result<()> {
    // Create new training job
    // Initialize escrow
    // Set initial state
}

pub fn register_participant(ctx: Context<RegisterParticipant>) -> Result<()> {
    // Register node for job
    // Lock stake tokens
}

pub fn submit_gradient(ctx: Context<SubmitGradient>, round_id: u64, gradient_hash: [u8; 32]) -> Result<()> {
    // Submit gradient update
    // Verify proof of training
}

pub fn complete_round(ctx: Context<CompleteRound>, round_id: u64, aggregated_gradients: Vec<u8>) -> Result<()> {
    // Aggregate gradients
    // Update model
    // Prepare rewards
}
```

#### Token Economics Program
```rust
// Program ID: TokeNecoNom1csForTrainingAndData1111111

// Accounts
#[account]
pub struct TokenPool {
    pub total_supply: u64,
    pub staked_tokens: u64,
    pub reward_pool: u64,
}

#[account]
pub struct StakeAccount {
    pub owner: Pubkey,
    pub amount: u64,
    pub staked_at: i64,
}

// Instructions
pub fn stake_tokens(ctx: Context<StakeTokens>, amount: u64) -> Result<()> {
    // Move tokens to stake
    // Update account
}

pub fn claim_rewards(ctx: Context<ClaimRewards>) -> Result<()> {
    // Calculate rewards
    // Transfer tokens
}

pub fn slash_stake(ctx: Context<SliceStake>, amount: u64, reason: SlashReason) -> Result<()> {
    // Reduce stake
    // Log reason
}
```

#### Model Registry Program
```rust
// Program ID: ModeLreg1stryForTrackedModels111111111

// Accounts
#[account]
pub struct Model {
    pub id: Pubkey,
    pub name: String,
    pub version: String,
    pub arweave_tx_id: String,
    pub owner: Pubkey,
    pub permissions: Vec<Permission>,
    pub benchmarks: Vec<Benchmark>,
    pub license: License,
}

// Instructions
pub fn register_model(ctx: Context<RegisterModel>, name: String, version: String, arweave_tx: String) -> Result<()> {
    // Register new model
    // Store metadata
}

pub fn update_benchmark(ctx: Context<UpdateBenchmark>, benchmark: Benchmark) -> Result<()> {
    // Update model benchmark
    // Verify authenticity
}
```

### 2. Training Framework

#### Model Abstraction
```python
from abc import ABC, abstractmethod

class BaseModel(ABC):
    """Abstract base class for all models"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
    
    @abstractmethod
    def load_weights(self, path):
        """Load model weights from storage"""
        pass
    
    @abstractmethod
    def save_weights(self, path):
        """Save model weights to storage"""
        pass
    
    @abstractmethod
    def forward(self, inputs):
        """Forward pass through the model"""
        pass
    
    @abstractmethod
    def compute_gradients(self, inputs, targets):
        """Compute gradients for training step"""
        pass
    
    @abstractmethod
    def apply_gradients(self, gradients):
        """Apply gradients to update model"""
        pass

class QwenSLMAdapter(BaseModel):
    """Adapter for Qwen Small Language Models"""
    
    def __init__(self, config):
        super().__init__(config)
        # Initialize Qwen model based on config
        self.model = self._initialize_qwen_model()
    
    def _initialize_qwen_model(self):
        """Initialize Qwen model with specified parameters"""
        # Load Qwen model with appropriate size
        # Apply LoRA if specified
        pass
    
    def load_weights(self, path):
        """Load Qwen model weights"""
        # Load from Arweave via tx_id in path
        pass
    
    def save_weights(self, path):
        """Save Qwen model weights"""
        # Save to local storage for upload to Arweave
        pass
    
    def forward(self, inputs):
        """Forward pass through Qwen model"""
        # Tokenize inputs
        # Run through model
        # Return outputs
        pass
    
    def compute_gradients(self, inputs, targets):
        """Compute gradients using Qwen's architecture"""
        # Forward pass
        # Compute loss
        # Backward pass
        # Return gradients
        pass
    
    def apply_gradients(self, gradients):
        """Apply gradients to Qwen model"""
        # Apply gradient updates
        # Handle LoRA specific updates
        pass
```

#### Dataset Management
```python
class DataProvider(ABC):
    """Abstract base class for data providers"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def get_training_batch(self, batch_size):
        """Get a batch of training data"""
        pass
    
    @abstractmethod
    def get_validation_batch(self, batch_size):
        """Get a batch of validation data"""
        pass

class WikiTextProvider(DataProvider):
    """Provider for WikiText dataset"""
    
    def __init__(self, config):
        super().__init__(config)
        self.dataset = self._load_wikitext()
    
    def _load_wikitext(self):
        """Load WikiText dataset"""
        # Download and process WikiText
        pass
    
    def get_training_batch(self, batch_size):
        """Get training batch from WikiText"""
        # Sample random batch
        # Tokenize and format
        pass
    
    def get_validation_batch(self, batch_size):
        """Get validation batch from WikiText"""
        # Sample validation batch
        # Tokenize and format
        pass

class SyntheticDataProvider(DataProvider):
    """Provider for synthetic data"""
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_training_batch(self, batch_size):
        """Generate synthetic training data"""
        # Generate text based on config
        pass
    
    def get_validation_batch(self, batch_size):
        """Generate synthetic validation data"""
        # Generate validation text
        pass
```

#### Gradient Compression
```python
import torch
import numpy as np

class GradientCompressor:
    """Compress gradients for efficient transmission"""
    
    def __init__(self, config):
        self.config = config
    
    def compress(self, gradients):
        """Compress gradients through multiple stages"""
        # Stage 1: Mixed precision (bf16)
        compressed = self._mixed_precision(gradients)
        
        # Stage 2: Quantization to int8
        compressed = self._quantize(compressed)
        
        # Stage 3: TopK sparsification
        compressed = self._sparsify(compressed)
        
        # Stage 4: Delta compression
        compressed = self._delta_compress(compressed)
        
        # Stage 5: Encryption
        compressed = self._encrypt(compressed)
        
        return compressed
    
    def decompress(self, compressed_gradients):
        """Decompress gradients"""
        # Reverse encryption
        gradients = self._decrypt(compressed_gradients)
        
        # Reverse delta compression
        gradients = self._delta_decompress(gradients)
        
        # Reverse sparsification
        gradients = self._desparsify(gradients)
        
        # Reverse quantization
        gradients = self._dequantize(gradients)
        
        # Convert back to full precision
        gradients = self._full_precision(gradients)
        
        return gradients
    
    def _mixed_precision(self, gradients):
        """Convert to bf16 for reduced size"""
        # Implementation
        pass
    
    def _quantize(self, gradients):
        """Quantize to int8 with error correction"""
        # Implementation
        pass
    
    def _sparsify(self, gradients):
        """Keep only top K gradients"""
        # Implementation
        pass
    
    def _delta_compress(self, gradients):
        """Compress against previous round"""
        # Implementation
        pass
    
    def _encrypt(self, gradients):
        """Encrypt before transmission"""
        # Implementation
        pass
```

### 3. Model Storage (Arweave + Solana)

#### Storage Client
```python
import arweave
import json

class ArweaveStorage:
    """Handle model storage on Arweave"""
    
    def __init__(self, wallet_path):
        self.wallet = arweave.Wallet(wallet_path)
        self.client = arweave.ArweaveClient()
    
    def upload_model(self, model_path, metadata):
        """Upload model weights to Arweave"""
        # Upload model file
        with open(model_path, 'rb') as f:
            model_data = f.read()
        
        tx = arweave.Transaction(self.wallet, data=model_data)
        tx.add_tag('Content-Type', 'application/octet-stream')
        tx.add_tag('App-Name', 'SolanaLM')
        tx.add_tag('Model-Metadata', json.dumps(metadata))
        tx.sign()
        tx.send()
        
        return tx.id
    
    def download_model(self, tx_id, save_path):
        """Download model weights from Arweave"""
        data = self.client.get_data(tx_id)
        with open(save_path, 'wb') as f:
            f.write(data)
    
    def get_metadata(self, tx_id):
        """Get model metadata from transaction"""
        tx = self.client.get_transaction(tx_id)
        metadata_tag = next((tag for tag in tx.tags if tag.name == 'Model-Metadata'), None)
        if metadata_tag:
            return json.loads(metadata_tag.value)
        return None

class ModelRegistry:
    """Interface with Solana Model Registry Program"""
    
    def __init__(self, program_id, payer):
        self.program_id = program_id
        self.payer = payer
    
    def register_model(self, name, version, arweave_tx_id):
        """Register model on Solana"""
        # Create instruction to register model
        # Send transaction
        pass
    
    def get_model_info(self, model_id):
        """Get model information from Solana"""
        # Query account data
        pass
    
    def update_benchmark(self, model_id, benchmark):
        """Update model benchmark"""
        # Create instruction to update benchmark
        # Send transaction
        pass
```

### 4. Inference Gateway (OpenAI Compatible)

#### API Server
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import torch

app = FastAPI(title="SolanaLM Inference API", version="1.0.0")

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 100
    stream: Optional[bool] = False

class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage

class ModelManager:
    """Manage loaded models for inference"""
    
    def __init__(self):
        self.loaded_models = {}
        self.model_cache = {}
    
    def load_model(self, model_id):
        """Load model if not already loaded"""
        if model_id not in self.loaded_models:
            # Get model info from registry
            # Download from Arweave if needed
            # Load into memory
            pass
        return self.loaded_models[model_id]
    
    def run_inference(self, model_id, inputs, params):
        """Run inference on loaded model"""
        model = self.load_model(model_id)
        # Process inputs
        # Run model
        # Return outputs
        pass

model_manager = ModelManager()

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI compatible chat completions endpoint"""
    try:
        # Validate model exists and user has access
        # Process messages into model inputs
        # Run inference
        # Format response
        
        response = ChatCompletionResponse(
            id="chatcmpl-" + str(hash(str(request.messages))),
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content="This is a sample response from SolanaLM"
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models"""
    # Query Solana for registered models
    # Return model list
    pass

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get information about a specific model"""
    # Query Solana for model info
    # Return model details
    pass
```

### 5. Network Coordination

#### Federated Learning Coordinator
```python
import asyncio
import random
from typing import List

class FederatedCoordinator:
    """Coordinate federated learning rounds"""
    
    def __init__(self, solana_client, model_registry):
        self.solana_client = solana_client
        self.model_registry = model_registry
        self.active_jobs = {}
    
    async def initialize_job(self, model_spec, data_req, reward_pool):
        """Initialize a new training job"""
        # Create job on Solana
        # Initialize model storage
        # Set up communication channels
        pass
    
    async def start_round(self, job_id, participants):
        """Start a new training round"""
        # Select participants based on reputation
        # Notify participants of round start
        # Distribute current model weights
        pass
    
    async def collect_gradients(self, job_id, round_id):
        """Collect gradients from participants"""
        # Wait for gradient submissions
        # Validate submissions
        # Handle late or missing submissions
        pass
    
    async def aggregate_gradients(self, job_id, round_id, gradients):
        """Aggregate gradients from participants"""
        # Apply reputation weighting
        # Compute aggregated gradients
        # Update global model
        pass
    
    async def complete_round(self, job_id, round_id, aggregated_gradients):
        """Complete round and prepare for next"""
        # Update model on storage
        # Distribute rewards
        # Prepare for next round or job completion
        pass

class TrainerNode:
    """Trainer node implementation"""
    
    def __init__(self, config, solana_client):
        self.config = config
        self.solana_client = solana_client
        self.model = None
        self.data_provider = None
        self.compressor = GradientCompressor(config)
    
    async def register_for_job(self, job_id):
        """Register to participate in a training job"""
        # Register with coordinator
        # Lock stake tokens
        pass
    
    async def participate_in_round(self, job_id, round_id):
        """Participate in a training round"""
        # Download latest model
        # Perform local training
        # Compute and compress gradients
        # Submit gradients to coordinator
        pass
    
    async def local_training(self, model, data_provider, rounds=1):
        """Perform local training rounds"""
        for _ in range(rounds):
            # Get training batch
            batch = data_provider.get_training_batch(self.config.batch_size)
            # Compute gradients
            gradients = model.compute_gradients(batch.inputs, batch.targets)
            # Apply gradients
            model.apply_gradients(gradients)
        return model
```

## Integration Points

### 1. Smart Contracts ↔ Training Framework
```python
class SolanaInterface:
    """Interface between training framework and Solana programs"""
    
    def __init__(self, rpc_url, payer_wallet):
        self.client = Client(rpc_url)
        self.payer = payer_wallet
        self.training_program = Program(training_coordinator_id, training_idl, self.client)
        self.token_program = Program(token_economics_id, token_idl, self.client)
        self.model_program = Program(model_registry_id, model_idl, self.client)
    
    def initialize_training_job(self, model_spec, data_req, reward_pool):
        """Initialize training job on Solana"""
        # Create instruction
        # Send transaction
        # Return job ID
        pass
    
    def submit_gradient(self, job_id, round_id, gradient_hash, proof):
        """Submit gradient to coordinator"""
        # Create instruction
        # Send transaction
        pass
    
    def claim_rewards(self, amount):
        """Claim earned rewards"""
        # Create instruction
        # Send transaction
        pass
```

### 2. Model Storage ↔ Training Framework
```python
class ModelStorageInterface:
    """Interface between training framework and model storage"""
    
    def __init__(self, arweave_wallet, solana_program):
        self.arweave = ArweaveStorage(arweave_wallet)
        self.registry = ModelRegistry(solana_program)
    
    def save_model_weights(self, model, metadata):
        """Save model weights to storage"""
        # Save locally first
        local_path = "/tmp/model_weights.pth"
        model.save_weights(local_path)
        # Upload to Arweave
        tx_id = self.arweave.upload_model(local_path, metadata)
        # Register on Solana
        self.registry.register_model(metadata['name'], metadata['version'], tx_id)
        return tx_id
    
    def load_model_weights(self, model_id):
        """Load model weights from storage"""
        # Get model info from Solana
        model_info = self.registry.get_model_info(model_id)
        # Download from Arweave
        local_path = f"/tmp/{model_id}.pth"
        self.arweave.download_model(model_info['arweave_tx_id'], local_path)
        # Load into model
        model = BaseModel(model_info['config'])
        model.load_weights(local_path)
        return model
```

### 3. Inference Gateway ↔ Model Storage
```python
class InferenceStorageInterface:
    """Interface between inference gateway and model storage"""
    
    def __init__(self, arweave_wallet, solana_program):
        self.arweave = ArweaveStorage(arweave_wallet)
        self.registry = ModelRegistry(solana_program)
        self.cache = {}
    
    def get_model_for_inference(self, model_id):
        """Get model ready for inference"""
        # Check cache first
        if model_id in self.cache:
            return self.cache[model_id]
        
        # Get model info from Solana
        model_info = self.registry.get_model_info(model_id)
        
        # Download from Arweave if needed
        local_path = f"/tmp/inference_{model_id}.pth"
        self.arweave.download_model(model_info['arweave_tx_id'], local_path)
        
        # Load model for inference (optimized)
        model = self._load_for_inference(local_path, model_info)
        
        # Cache for future requests
        self.cache[model_id] = model
        
        return model
    
    def _load_for_inference(self, model_path, model_info):
        """Load model optimized for inference"""
        # Load with optimizations (quantization, etc.)
        # Move to appropriate device (GPU/CPU)
        pass
```

## Security Considerations

### 1. Data Privacy
- Raw training data never leaves data provider's infrastructure
- Only gradient updates are shared (not original data)
- Differential privacy noise can be added to gradients
- Secure aggregation prevents coordinator from seeing individual gradients

### 2. Model Security
- Access control through Solana programs
- Licensing and permissions management
- Encryption of model weights in storage
- Secure key management for Arweave

### 3. Network Security
- Authentication for all API endpoints
- Rate limiting to prevent abuse
- Secure communication between nodes
- Byzantine fault tolerance in federated learning

## Performance Requirements

### 1. Training Performance
- Round duration: 10-30 minutes
- Support for 20-100 nodes per round
- Gradient compression reducing data size by 90%+
- Model quality within 5% of centralized equivalents

### 2. Inference Performance
- Response latency <2 seconds for typical requests
- Support for concurrent requests
- Caching for frequently accessed models
- Resource management to prevent overload

### 3. Storage Performance
- Model upload/download <5 minutes for typical SLMs
- Cost-effective storage under $25 per model upload
- Redundancy and availability guarantees
- Metadata queries <1 second

## Testing Strategy

### 1. Unit Testing
- Smart contract instruction tests
- Model loading and gradient computation
- Compression and encryption algorithms
- API endpoint validation

### 2. Integration Testing
- End-to-end training job flow
- Reward distribution mechanisms
- Model storage and retrieval
- Inference API compatibility

### 3. Performance Testing
- Network coordination with multiple nodes
- Gradient compression/decompression speed
- Model loading and inference latency
- Storage upload/download performance

### 4. Security Testing
- Smart contract vulnerability assessment
- Data privacy verification
- Access control testing
- Network attack simulation

## Success Metrics

### 1. Technical Metrics
- All smart contracts deployed and functional
- Training framework supports federated learning
- Model storage system handles uploads/downloads
- Inference gateway compatible with OpenAI API
- Network coordinates 20+ nodes successfully

### 2. Performance Metrics
- 95%+ uptime for core services
- <2 second inference latency
- 99.9% gradient aggregation success rate
- <0.1% Byzantine participant rate

### 3. Operational Metrics
- 20 active trainer nodes
- 5 specialized models deployed
- Positive feedback from beta testers
- Documentation enables self-service onboarding

This comprehensive technical specification provides all the details needed to implement Phase 1 of SolanaLM with a focus on eliminating unknowns for technical adoption. All core components are specified with clear interfaces and integration points, ensuring a cohesive system that addresses dataset management, model storage, and inference compatibility.