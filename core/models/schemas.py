"""
Data models and schemas for SolanaLM network
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
import uuid


class NodeType(str, Enum):
    """Types of nodes in the network"""
    INFERENCE = "inference"
    TRAINING = "training"
    HYBRID = "hybrid"
    PROXY = "proxy"


class ModelType(str, Enum):
    """Supported model types"""
    QWEN_SLM = "qwen-slm"
    CUSTOM = "custom"
    OPENAI_GPT = "openai-gpt"
    ANTHROPIC_CLAUDE = "anthropic-claude"


class NodeStatus(str, Enum):
    """Node operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


# Request/Response Models

class InferenceRequest(BaseModel):
    """Request for LLM inference"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., description="Input prompt")
    max_tokens: int = Field(default=100, ge=1, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    wallet_address: str = Field(..., description="Solana wallet for payment")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    """Response from LLM inference"""
    request_id: str
    model: str
    response: str
    processing_time: float
    tokens_generated: int
    cost_sol: float
    node_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Node Models

class HardwareSpecs(BaseModel):
    """Hardware specifications for a node"""
    gpu_model: Optional[str] = None
    gpu_memory_gb: Optional[int] = None
    cpu_cores: int = Field(..., ge=1)
    ram_gb: int = Field(..., ge=4)
    storage_gb: int = Field(..., ge=100)
    network_speed_mbps: int = Field(..., ge=10)


class PricingConfig(BaseModel):
    """Pricing configuration for node services"""
    per_request: float = Field(..., description="SOL per inference request")
    per_token: float = Field(..., description="SOL per generated token")
    per_training_round: float = Field(default=0.0, description="SOL per training round")
    minimum_payment: float = Field(default=0.001, description="Minimum SOL payment")


class NodeCapabilities(BaseModel):
    """Node capabilities and configuration"""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType
    wallet_address: str = Field(..., description="Solana wallet address")
    endpoint_url: str = Field(..., description="Node API endpoint")

    # Hardware and performance
    hardware: HardwareSpecs
    pricing: PricingConfig

    # Supported models
    supported_models: List[str] = Field(..., min_items=1)
    max_concurrent_requests: int = Field(default=1, ge=1)

    # Status and metrics
    status: NodeStatus = Field(default=NodeStatus.ONLINE)
    reputation_score: float = Field(default=1.0, ge=0.0, le=1.0)
    total_requests_served: int = Field(default=0, ge=0)
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    average_response_time: float = Field(default=0.0, ge=0.0)

    # Registration info
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class TrainingRound(BaseModel):
    """Federated learning training round"""
    round_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model: str = Field(..., description="Model being trained")
    participating_nodes: List[str] = Field(..., description="Node IDs")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: int = Field(..., ge=1)
    reward_per_node: float = Field(..., description="SOL reward per participant")
    status: str = Field(default="scheduled")


class TrainingUpdate(BaseModel):
    """Training update from federated learning node"""
    node_id: str
    round_id: str
    model_weights: Dict[str, Any] = Field(..., description="Model weight updates")
    training_metrics: Dict[str, Any] = Field(..., description="Training performance metrics")
    update_size_mb: float = Field(..., description="Size of update in MB")
    compression_method: Optional[str] = Field(default=None, description="Compression method used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GradientUpdate(BaseModel):
    """Gradient update from training node"""
    node_id: str
    round_id: str
    gradient_hash: str = Field(..., description="SHA256 hash of gradients")
    gradient_size_bytes: int
    upload_url: str = Field(..., description="IPFS/Arweave URL for gradients")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Payment Models

class PaymentRequest(BaseModel):
    """Payment request for services"""
    from_wallet: str = Field(..., description="Payer's wallet address")
    to_wallet: str = Field(..., description="Recipient's wallet address")
    amount_sol: float = Field(..., gt=0, description="Payment amount in SOL")
    service_type: str = Field(..., description="Type of service being paid for")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentResult(BaseModel):
    """Result of payment processing"""
    transaction_signature: str
    amount_sol: float
    from_wallet: str
    to_wallet: str
    block_height: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="confirmed")


# Network Statistics

class NetworkStats(BaseModel):
    """Overall network statistics"""
    total_nodes: int = 0
    active_nodes: int = 0
    inference_nodes: int = 0
    training_nodes: int = 0
    hybrid_nodes: int = 0
    proxy_nodes: int = 0
    total_requests_24h: int = 0
    active_training_rounds: int = 0
    total_models_available: int = 0
    average_response_time: float = 0.0
    network_uptime: float = 1.0