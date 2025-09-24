"""
Configuration Management for SolanaLM

Centralized configuration for all network components.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
from enum import Enum


class NetworkEnvironment(str, Enum):
    """Network environment types"""
    DEVELOPMENT = "development"
    TESTNET = "testnet"
    MAINNET = "mainnet"


class SolanaLMConfig(BaseSettings):
    """Main configuration for SolanaLM network"""

    # Environment
    environment: NetworkEnvironment = Field(
        default=NetworkEnvironment.DEVELOPMENT,
        env="SOLANALM_ENVIRONMENT"
    )

    # Solana Configuration
    solana_network: str = Field(
        default="devnet",
        env="SOLANA_NETWORK",
        description="Solana network: devnet, testnet, mainnet-beta"
    )
    solana_rpc_url: str = Field(
        default="https://api.devnet.solana.com",
        env="SOLANA_RPC_URL"
    )

    # Gateway Configuration
    gateway_host: str = Field(default="0.0.0.0", env="GATEWAY_HOST")
    gateway_port: int = Field(default=8001, env="GATEWAY_PORT")
    gateway_workers: int = Field(default=1, env="GATEWAY_WORKERS")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://solanalm:solanalm@localhost:5432/solanalm",
        env="DATABASE_URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )

    # Node Configuration
    min_training_participants: int = Field(default=3, env="MIN_TRAINING_PARTICIPANTS")
    max_training_participants: int = Field(default=20, env="MAX_TRAINING_PARTICIPANTS")
    training_round_duration_minutes: int = Field(default=15, env="TRAINING_ROUND_DURATION")

    # Pricing Configuration
    base_inference_cost_sol: float = Field(default=0.001, env="BASE_INFERENCE_COST_SOL")
    base_training_reward_sol: float = Field(default=0.1, env="BASE_TRAINING_REWARD_SOL")
    proxy_markup_multiplier: float = Field(default=2.0, env="PROXY_MARKUP_MULTIPLIER")

    # API Keys (optional - for proxy nodes)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")

    # Security
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    admin_api_key: str = Field(
        default="admin-key-change-in-production",
        env="ADMIN_API_KEY"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # Health Check Configuration
    node_health_check_interval: int = Field(default=30, env="NODE_HEALTH_CHECK_INTERVAL")
    node_timeout_seconds: int = Field(default=60, env="NODE_TIMEOUT_SECONDS")

    # Model Storage
    model_storage_path: str = Field(default="./models", env="MODEL_STORAGE_PATH")
    gradient_storage_url: str = Field(
        default="",
        env="GRADIENT_STORAGE_URL",
        description="IPFS or Arweave endpoint for gradient storage"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


class NodeConfig(BaseSettings):
    """Configuration for individual nodes"""

    # Node Identity
    node_id: str = Field(..., env="NODE_ID")
    wallet_address: str = Field(..., env="WALLET_ADDRESS")
    node_type: str = Field(..., env="NODE_TYPE")  # inference, training, hybrid, proxy

    # Network
    gateway_url: str = Field(default="http://localhost:8001", env="GATEWAY_URL")
    node_host: str = Field(default="0.0.0.0", env="NODE_HOST")
    node_port: int = Field(default=8100, env="NODE_PORT")

    # Hardware (auto-detected if not specified)
    gpu_enabled: bool = Field(default=True, env="GPU_ENABLED")
    max_concurrent_requests: int = Field(default=1, env="MAX_CONCURRENT_REQUESTS")

    # Model Configuration
    model_name: str = Field(
        default="microsoft/DialoGPT-small",
        env="MODEL_NAME"
    )
    supported_models: str = Field(
        default="",
        env="SUPPORTED_MODELS",
        description="Comma-separated list of supported models"
    )

    # Pricing
    price_per_request: float = Field(default=0.001, env="PRICE_PER_REQUEST")
    price_per_token: float = Field(default=0.0001, env="PRICE_PER_TOKEN")
    minimum_payment: float = Field(default=0.0005, env="MINIMUM_PAYMENT")

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> SolanaLMConfig:
    """Get the main application settings"""
    return SolanaLMConfig()


def get_node_config() -> NodeConfig:
    """Get node-specific configuration"""
    return NodeConfig()


# Network-specific configurations
NETWORK_CONFIGS = {
    NetworkEnvironment.DEVELOPMENT: {
        "solana_rpc_url": "http://localhost:8899",  # Local validator
        "database_url": "sqlite:///./solanalm_dev.db",
        "log_level": "DEBUG",
        "min_training_participants": 2,  # Lower for testing
    },
    NetworkEnvironment.TESTNET: {
        "solana_rpc_url": "https://api.testnet.solana.com",
        "database_url": "postgresql://solanalm:solanalm@localhost:5432/solanalm_testnet",
        "log_level": "INFO",
        "min_training_participants": 3,
    },
    NetworkEnvironment.MAINNET: {
        "solana_rpc_url": "https://api.mainnet-beta.solana.com",
        "database_url": "postgresql://solanalm:solanalm@prod-db:5432/solanalm_prod",
        "log_level": "WARNING",
        "min_training_participants": 5,
    }
}


def get_network_config(environment: NetworkEnvironment) -> Dict[str, Any]:
    """Get configuration overrides for specific network environment"""
    return NETWORK_CONFIGS.get(environment, {})


# Default model configurations
DEFAULT_MODELS = {
    "qwen-slm": {
        "name": "Qwen/Qwen-1_8B-Chat",
        "type": "causal_lm",
        "max_length": 2048,
        "pricing": {
            "per_request": 0.002,
            "per_token": 0.0002
        }
    },
    "dialog-gpt": {
        "name": "microsoft/DialoGPT-small",
        "type": "causal_lm",
        "max_length": 1024,
        "pricing": {
            "per_request": 0.001,
            "per_token": 0.0001
        }
    },
    "openai-gpt-3.5": {
        "name": "gpt-3.5-turbo",
        "type": "proxy",
        "provider": "openai",
        "pricing": {
            "per_request": 0.01,
            "per_token": 0.0005
        }
    }
}


def get_model_config(model_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific model"""
    return DEFAULT_MODELS.get(model_name)


# Utility functions for configuration validation
def validate_solana_address(address: str) -> bool:
    """Validate Solana wallet address format"""
    try:
        from solana.publickey import PublicKey
        PublicKey(address)
        return True
    except Exception:
        return False


def validate_environment_variables():
    """Validate that required environment variables are set"""
    required_vars = []
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Configuration constants
DEFAULT_TIMEOUT_SECONDS = 60
MAX_REQUEST_SIZE_MB = 10
MAX_MODEL_SIZE_GB = 50
DEFAULT_BATCH_SIZE = 1
MAX_CONCURRENT_TRAINING_ROUNDS = 5

# Supported model types
SUPPORTED_MODEL_TYPES = [
    "causal_lm",        # GPT-like models
    "seq2seq",          # T5-like models
    "proxy"             # External API proxy
]

# Supported Solana networks
SUPPORTED_SOLANA_NETWORKS = [
    "devnet",
    "testnet",
    "mainnet-beta",
    "localhost"
]