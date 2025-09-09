# Phase 1 Technical Specification: Complete System Integration (Revised with Distributed Inference)

## Overview

This document specifies the complete technical implementation for Phase 1 of SolanaLM, integrating all core components to eliminate unknowns for technical adoption. The specification covers dataset management, decentralized model storage, inference gateway, distributed inference, and all integration points.

**NOTE: This document has been revised to reflect a fully decentralized model storage approach, eliminating reliance on centralized storage providers like Arweave, and includes distributed inference capabilities.**

## System Architecture

### High-Level Components

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Trainer Node  │    │  Coordinator     │    │ Inference        │
│  (Model Owner)  │    │  (Solana)        │    │  Requestor       │
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
│  Dataset        │    │  Model Registry  │    │  Request         │
│  Management     │    │  (Solana)        │    │  Distribution    │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         ▲                       │                        ▲
         │                       ▼                        │
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Local Data     │    │  Peer-to-Peer    │    │  Response        │
│  Processing     │    │  Distribution    │    │  Aggregation     │
└─────────────────┘    │  Protocol        │    └──────────────────┘
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Model Replica & │
                       │  Inference Nodes │
                       └──────────────────┘
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
    pub owner: Pubkey,
    pub architecture: String,
    pub domain: String,
    pub replicas: Vec<NodeInfo>,  // List of nodes storing this model
    pub inference_nodes: Vec<NodeInfo>,  // List of nodes authorized for inference
    pub permissions: Vec<Permission>,
    pub inference_permissions: InferencePermissions,  // New field
    pub benchmarks: Vec<Benchmark>,
    pub license: License,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeInfo {
    pub node_id: Pubkey,
    pub ip_address: String,
    pub port: u16,
    pub last_heartbeat: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct InferencePermissions {
    pub distributed_inference_allowed: bool,
    pub authorized_nodes: Vec<Pubkey>,
    pub max_concurrent_requests: u32,
    pub rate_limits: RateLimits,
    pub reward_sharing_percentage: u8,  // 0-100
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct RateLimits {
    pub requests_per_minute: u32,
    pub tokens_per_minute: u32,
}

// Instructions
pub fn register_model(ctx: Context<RegisterModel>, name: String, version: String, architecture: String, domain: String) -> Result<()> {
    // Register new model
    // Store metadata
    // Initialize empty replicas list
}

pub fn update_benchmark(ctx: Context<UpdateBenchmark>, benchmark: Benchmark) -> Result<()> {
    // Update model benchmark
    // Verify authenticity
}

pub fn add_replica(ctx: Context<AddReplica>, node_info: NodeInfo) -> Result<()> {
    // Add node to model replicas list
    // Verify node can serve model
}

pub fn remove_replica(ctx: Context<RemoveReplica>, node_id: Pubkey) -> Result<()> {
    // Remove node from replicas list
    // Handle graceful removal
}

// New instructions for distributed inference
pub fn set_inference_permissions(ctx: Context<SetInferencePermissions>, permissions: InferencePermissions) -> Result<()> {
    // Set inference permissions for a model
    // Only model owner can call this
}

pub fn register_inference_node(ctx: Context<RegisterInferenceNode>, node_info: NodeInfo) -> Result<()> {
    // Register node for inference serving
    // Must be authorized by model owner
}

pub fn report_inference_usage(ctx: Context<ReportInferenceUsage>, usage: InferenceUsage) -> Result<()> {
    // Report inference usage for reward calculation
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
        # Load from local storage
        pass
    
    def save_weights(self, path):
        """Save Qwen model weights"""
        # Save to local storage
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

class DeveloperDataProvider(DataProvider):
    """Developer's custom data provider implementation"""
    
    def __init__(self, data_path, config):
        super().__init__(config)
        self.data_path = data_path
        self.dataset = self._load_dataset()
    
    def _load_dataset(self):
        """Load developer's dataset"""
        # Implementation specific to developer's data format
        pass
    
    def get_training_batch(self, batch_size):
        """Get a batch of training data"""
        # Sample and preprocess data batch
        # Return in standard format
        pass
    
    def get_validation_batch(self, batch_size):
        """Get a batch of validation data"""
        # Sample and preprocess validation batch
        # Return in standard format
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

### 3. Decentralized Model Storage

#### Peer-to-Peer Storage Client
```python
import json
import requests
from typing import List

class P2PModelStorage:
    """Decentralized model storage and distribution"""
    
    def __init__(self, solana_client):
        self.solana_client = solana_client
        self.local_cache = {}
        self.replication_targets = []
    
    def publish_model(self, model, metadata):
        """Publish trained model to the network"""
        # Save model locally
        model_path = self._save_model_locally(model, metadata)
        
        # Register on Solana
        model_id = self._register_on_solana(metadata)
        
        # Announce availability to network
        self._announce_availability(model_id, model_path)
        
        return model_id
    
    def download_model(self, model_id):
        """Download model from the network"""
        # Check local cache first
        if model_id in self.local_cache:
            return self.local_cache[model_id]
        
        # Get model info from Solana
        model_info = self._get_model_info(model_id)
        
        # Find nearest replica
        replica = self._find_nearest_replica(model_info['replicas'])
        
        # Download from replica
        model = self._download_from_replica(replica, model_id)
        
        # Cache locally
        self.local_cache[model_id] = model
        
        return model
    
    def replicate_model(self, model_id):
        """Replicate model to this node"""
        # Download model
        model = self.download_model(model_id)
        
        # Save locally
        model_path = self._save_model_locally(model)
        
        # Update Solana with replica info
        self._update_replica_info(model_id, model_path)
        
        return model_path
    
    def _save_model_locally(self, model, metadata=None):
        """Save model to local storage"""
        # Implementation for saving model weights locally
        pass
    
    def _register_on_solana(self, metadata):
        """Register model on Solana blockchain"""
        # Create instruction to register model
        # Send transaction
        # Return model ID
        pass
    
    def _announce_availability(self, model_id, model_path):
        """Announce model availability to network"""
        # Send announcement to coordinator
        # Update peer list
        pass
    
    def _get_model_info(self, model_id):
        """Get model information from Solana"""
        # Query Solana program for model metadata
        pass
    
    def _find_nearest_replica(self, replicas: List[dict]):
        """Find nearest replica based on network topology"""
        # Implementation for replica selection
        pass
    
    def _download_from_replica(self, replica, model_id):
        """Download model from a replica node"""
        # HTTP request to replica node
        # Stream download of model weights
        pass
    
    def _update_replica_info(self, model_id, model_path):
        """Update replica information on Solana"""
        # Add this node to model's replica list
        pass

class ModelRegistryInterface:
    """Interface with Solana Model Registry Program"""
    
    def __init__(self, program_id, payer):
        self.program_id = program_id
        self.payer = payer
    
    def register_model(self, name, version, architecture, domain):
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
    
    def add_replica(self, model_id, node_info):
        """Add node as model replica"""
        # Create instruction to add replica
        # Send transaction
        pass
    
    def set_inference_permissions(self, model_id, permissions):
        """Set inference permissions for a model"""
        # Create instruction to set inference permissions
        # Send transaction
        pass
    
    def register_inference_node(self, model_id, node_info):
        """Register node for inference serving"""
        # Create instruction to register inference node
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
    
    def __init__(self, solana_client):
        self.solana_client = solana_client
        self.loaded_models = {}
        self.model_cache = {}
        self.storage = P2PModelStorage(solana_client)
        self.inference_coordinator = DistributedInferenceCoordinator(solana_client)
    
    def load_model(self, model_id):
        """Load model if not already loaded"""
        if model_id not in self.loaded_models:
            # Download from network if needed
            model = self.storage.download_model(model_id)
            # Load into memory
            self.loaded_models[model_id] = model
        return self.loaded_models[model_id]
    
    def run_inference(self, model_id, inputs, params):
        """Run inference on loaded model"""
        # Check if distributed inference is allowed
        model_info = self.storage.get_model_info(model_id)
        if (model_info.get('inference_permissions', {}).get('distributed_inference_allowed', False) and
            len(model_info.get('inference_nodes', [])) > 0):
            # Use distributed inference
            return self.inference_coordinator.route_inference_request(model_id, inputs, params)
        else:
            # Use local inference
            model = self.load_model(model_id)
            # Process inputs
            # Run model
            # Return outputs
            pass

model_manager = ModelManager(solana_client)

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

### 5. Distributed Inference System

#### Distributed Inference Coordinator
```python
import asyncio
import random
from typing import List
import copy

class DistributedInferenceCoordinator:
    """Coordinate distributed inference requests"""
    
    def __init__(self, solana_client):
        self.solana_client = solana_client
        self.node_registry = {}
        self.load_balancer = LoadBalancer()
        self.request_distributor = RequestDistributor()
    
    def route_inference_request(self, model_id, inputs, params):
        """Route inference request to appropriate nodes"""
        # Get model permissions
        permissions = self._get_model_permissions(model_id)
        
        # Check if distributed inference is allowed
        if not permissions.distributed_inference_allowed:
            # Route to model owner's node
            return self._route_to_owner(model_id, inputs, params)
        
        # Get available nodes for this model
        available_nodes = self._get_authorized_nodes(model_id)
        
        # Create request object
        request = InferenceRequest(model_id, inputs, params)
        
        # Load balance across nodes
        selected_nodes = self.load_balancer.select_nodes(
            available_nodes, 
            request.complexity
        )
        
        # Distribute request if it's a batch that can be split
        if (self.request_distributor.can_distribute(request) and 
            len(selected_nodes) > 1):
            return self._distribute_request(selected_nodes, request)
        else:
            # Route to single node
            return self._route_to_single_node(selected_nodes[0], request)
    
    def _distribute_request(self, nodes, request):
        """Distribute a large inference request across multiple nodes"""
        # Split request into sub-requests
        sub_requests = self.request_distributor.split_request(request, len(nodes))
        
        # Send sub-requests to nodes
        responses = []
        for i, node in enumerate(nodes):
            response = node.process_inference(sub_requests[i])
            responses.append(response)
        
        # Aggregate responses
        return self.request_distributor.aggregate_responses(responses)
    
    def _get_model_permissions(self, model_id):
        """Get inference permissions for a model"""
        # Query Solana for model permissions
        pass
    
    def _get_authorized_nodes(self, model_id):
        """Get nodes authorized for inference"""
        # Query Solana for authorized nodes
        pass
    
    def _route_to_owner(self, model_id, inputs, params):
        """Route request to model owner"""
        # Get model owner info
        # Send request to owner's node
        pass
    
    def _route_to_single_node(self, node, request):
        """Route request to a single node"""
        # Send request to node
        # Return response
        pass

class LoadBalancer:
    """Load balance inference requests across nodes"""
    
    def __init__(self):
        self.node_metrics = {}
    
    def select_nodes(self, available_nodes, request_complexity):
        """Select nodes based on load and capabilities"""
        # Sort nodes by load and capabilities
        # Select appropriate number of nodes
        pass
    
    def update_node_metrics(self, node_id, metrics):
        """Update metrics for a node"""
        self.node_metrics[node_id] = metrics

class RequestDistributor:
    """Distribute large inference requests"""
    
    def __init__(self):
        self.max_batch_size_per_node = 32
    
    def can_distribute(self, request):
        """Determine if a request can be distributed"""
        return (hasattr(request, 'batch_size') and 
                request.batch_size > self.max_batch_size_per_node)
    
    def split_request(self, request, num_nodes):
        """Split a large request into smaller sub-requests"""
        if not hasattr(request, 'inputs'):
            return [request]
            
        # Split inputs across nodes
        input_chunks = self._chunk_inputs(request.inputs, num_nodes)
        
        sub_requests = []
        for i, chunk in enumerate(input_chunks):
            sub_request = copy.deepcopy(request)
            sub_request.inputs = chunk
            sub_request.request_id = f"{request.request_id}_part_{i}"
            sub_requests.append(sub_request)
            
        return sub_requests
    
    def aggregate_responses(self, responses):
        """Combine responses from multiple nodes"""
        # Sort responses by request_id to maintain order
        responses.sort(key=lambda r: r.request_id)
        
        # Combine outputs
        aggregated_output = []
        for response in responses:
            if hasattr(response, 'outputs'):
                aggregated_output.extend(response.outputs)
        
        # Create final response
        final_response = copy.deepcopy(responses[0])
        final_response.outputs = aggregated_output
        final_response.request_id = responses[0].request_id.split('_part_')[0]
        
        return final_response
    
    def _chunk_inputs(self, inputs, num_chunks):
        """Split inputs into chunks"""
        chunk_size = len(inputs) // num_chunks
        chunks = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size if i < num_chunks - 1 else len(inputs)
            chunks.append(inputs[start:end])
        return chunks

class InferenceRequest:
    """Represents an inference request"""
    
    def __init__(self, model_id, inputs, params):
        self.model_id = model_id
        self.inputs = inputs
        self.params = params
        self.request_id = f"req_{hash(str(inputs))}"
        self.batch_size = len(inputs) if hasattr(inputs, '__len__') else 1
        self.complexity = self._calculate_complexity()
    
    def _calculate_complexity(self):
        """Calculate request complexity"""
        # Implementation based on input size, model size, etc.
        return self.batch_size

class InferenceNode:
    """Represents an inference node in the network"""
    
    def __init__(self, node_id, capabilities):
        self.node_id = node_id
        self.capabilities = capabilities
        self.registered_models = {}
    
    def register_for_inference(self, model_id, permissions):
        """Register to serve inference for a model"""
        # Verify permissions from Solana
        # Add to registered models list
        # Update Solana program with node info
        pass
    
    def process_inference(self, request):
        """Process an inference request"""
        # Load model if not already loaded
        # Process inputs
        # Run inference
        # Return response
        pass
```

### 6. Network Coordination

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
        self.model_storage = P2PModelStorage(solana_client)
    
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
    
    async def fine_tune_on_developer_data(self, model_id, developer_data_provider):
        """Fine-tune model on developer's data"""
        # Load base model
        model = self.model_storage.download_model(model_id)
        
        # Fine-tune on developer's data
        fine_tuned_model = self.local_training(model, developer_data_provider)
        
        # Save and publish fine-tuned model
        metadata = {
            "name": f"fine-tuned-{model_id}",
            "version": "1.0.0",
            "base_model": model_id,
            "domain": "developer-specific"
        }
        
        fine_tuned_model_id = self.model_storage.publish_model(fine_tuned_model, metadata)
        
        return fine_tuned_model_id
    
    async def register_for_inference(self, model_id):
        """Register this node to serve inference for a model"""
        # Get model info
        model_info = self.model_storage.get_model_info(model_id)
        
        # Register with Solana
        node_info = {
            "node_id": self.solana_client.get_pubkey(),
            "ip_address": self.config.get("ip_address", "localhost"),
            "port": self.config.get("inference_port", 8000),
            "last_heartbeat": int(time.time())
        }
        
        self.model_storage.register_inference_node(model_id, node_info)
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
    
    def register_model(self, name, version, architecture, domain):
        """Register model on Solana"""
        # Create instruction
        # Send transaction
        pass
    
    def add_model_replica(self, model_id, node_info):
        """Add node as model replica"""
        # Create instruction
        # Send transaction
        pass
    
    def set_inference_permissions(self, model_id, permissions):
        """Set inference permissions for a model"""
        # Create instruction
        # Send transaction
        pass
    
    def register_inference_node(self, model_id, node_info):
        """Register node for inference serving"""
        # Create instruction
        # Send transaction
        pass
```

### 2. Model Storage ↔ Training Framework
```python
class ModelStorageInterface:
    """Interface between training framework and model storage"""
    
    def __init__(self, solana_program, solana_client):
        self.registry = ModelRegistryInterface(solana_program, solana_client)
        self.p2p_storage = P2PModelStorage(solana_client)
    
    def save_trained_model(self, model, metadata):
        """Save trained model to decentralized storage"""
        # Save locally first
        local_path = "/tmp/model_weights.pth"
        model.save_weights(local_path)
        # Publish to network
        model_id = self.p2p_storage.publish_model(model, metadata)
        return model_id
    
    def load_model_for_training(self, model_id):
        """Load model for training/fine-tuning"""
        # Download from network
        model = self.p2p_storage.download_model(model_id)
        return model
    
    def replicate_model(self, model_id):
        """Replicate model to this node"""
        return self.p2p_storage.replicate_model(model_id)
    
    def set_inference_permissions(self, model_id, permissions):
        """Set inference permissions for a model"""
        return self.registry.set_inference_permissions(model_id, permissions)
    
    def register_inference_node(self, model_id, node_info):
        """Register node for inference serving"""
        return self.registry.register_inference_node(model_id, node_info)
```

### 3. Inference Gateway ↔ Model Storage
```python
class InferenceStorageInterface:
    """Interface between inference gateway and model storage"""
    
    def __init__(self, solana_program, solana_client):
        self.p2p_storage = P2PModelStorage(solana_client)
        self.registry = ModelRegistryInterface(solana_program, solana_client)
        self.cache = {}
    
    def get_model_for_inference(self, model_id):
        """Get model ready for inference"""
        # Check cache first
        if model_id in self.cache:
            return self.cache[model_id]
        
        # Download from network
        model = self.p2p_storage.download_model(model_id)
        
        # Load model for inference (optimized)
        inference_model = self._load_for_inference(model)
        
        # Cache for future requests
        self.cache[model_id] = inference_model
        
        return inference_model
    
    def get_model_inference_permissions(self, model_id):
        """Get inference permissions for a model"""
        model_info = self.p2p_storage.get_model_info(model_id)
        return model_info.get('inference_permissions', {})
    
    def _load_for_inference(self, model):
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
- Encryption of model weights in transmission
- Secure key management for node authentication

### 3. Inference Security
- Authorization verified through Solana programs
- Input data encrypted in transit
- No storage of inference inputs on serving nodes
- Secure aggregation of distributed responses

### 4. Network Security
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
- Distributed inference for large batch requests

### 3. Storage Performance
- Model download <5 minutes for typical SLMs
- Efficient peer-to-peer distribution
- Replica selection based on network proximity
- Metadata queries <1 second

## Testing Strategy

### 1. Unit Testing
- Smart contract instruction tests
- Model loading and gradient computation
- Compression and encryption algorithms
- API endpoint validation
- Distributed inference routing logic

### 2. Integration Testing
- End-to-end training job flow
- Reward distribution mechanisms
- Model storage and retrieval
- Inference API compatibility
- Distributed inference workflows

### 3. Performance Testing
- Network coordination with multiple nodes
- Gradient compression/decompression speed
- Model loading and inference latency
- Peer-to-peer distribution performance
- Distributed inference scaling

### 4. Security Testing
- Smart contract vulnerability assessment
- Data privacy verification
- Access control testing
- Network attack simulation
- Inference security validation

## Success Metrics

### 1. Technical Metrics
- All smart contracts deployed and functional
- Training framework supports federated learning
- Decentralized model storage system operational
- Inference gateway compatible with OpenAI API
- Distributed inference capability working
- Network coordinates 20+ nodes successfully

### 2. Performance Metrics
- 95%+ uptime for core services
- <2 second inference latency (single node)
- <5 second inference latency (distributed)
- 99.9% gradient aggregation success rate
- <0.1% Byzantine participant rate

### 3. Operational Metrics
- 20 active trainer nodes
- 5 specialized models deployed
- Positive feedback from beta testers
- Documentation enables self-service onboarding
- Distributed inference requests processed successfully

This revised technical specification provides all the details needed to implement Phase 1 of SolanaLM with a fully decentralized approach that eliminates reliance on centralized storage providers and includes distributed inference capabilities. All core components are specified with clear interfaces and integration points, ensuring a cohesive system that addresses dataset management, decentralized model storage, inference compatibility, and distributed inference when permitted by model owners.