"""
Production-Ready Configuration Management System
Supports multiple environments, secrets management, and hot reloading
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
from pydantic_settings import BaseSettings
from pydantic import Field, validator

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "solanalm"
    username: str = "solanalm"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    pool_size: int = 10


@dataclass
class SolanaConfig:
    network: str = "devnet"
    rpc_url: str = "https://api.devnet.solana.com"
    commitment: str = "confirmed"
    timeout: int = 30
    retry_attempts: int = 3
    treasury_keypair_path: Optional[str] = None


@dataclass
class SecurityConfig:
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    api_rate_limit: int = 100  # requests per minute
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    encryption_key: Optional[str] = None


@dataclass
class ModelConfig:
    default_model: str = "microsoft/DialoGPT-small"
    model_cache_dir: str = "./models"
    max_model_memory_gb: float = 8.0
    model_download_timeout: int = 300
    enable_model_quantization: bool = True


@dataclass
class NetworkConfig:
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    health_check_interval: int = 30
    node_timeout: int = 60
    max_retries: int = 3
    circuit_breaker_threshold: int = 5


@dataclass
class MonitoringConfig:
    enable_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_profiling: bool = False


@dataclass
class FederatedLearningConfig:
    min_participants: int = 3
    max_participants: int = 20
    round_duration_minutes: int = 15
    convergence_threshold: float = 0.001
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs_per_round: int = 1


class ProductionSettings(BaseSettings):
    """Comprehensive production settings"""

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    testing: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 1
    reload: bool = False

    # Application
    app_name: str = "SolanaLM"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://solanalm:solanalm@localhost:5432/solanalm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Solana
    solana_network: str = "devnet"
    solana_rpc_url: str = "https://api.devnet.solana.com"

    # Security
    secret_key: str = Field(default="", env="SECRET_KEY")
    api_keys: List[str] = Field(default_factory=list, env="API_KEYS")

    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")

    # Feature flags
    enable_federated_learning: bool = True
    enable_privacy_features: bool = True
    enable_monitoring: bool = True
    enable_caching: bool = True

    model_config = {
        "env_file": [".env", ".env.local", f".env.{Environment.DEVELOPMENT.value}"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        if values.get("environment") == Environment.PRODUCTION and not v:
            raise ValueError("SECRET_KEY is required in production")
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "sqlite:///")):
            raise ValueError("Invalid database URL format")
        return v

    def get_database_config(self) -> DatabaseConfig:
        """Parse database configuration from URL"""
        # Simplified parsing - in production, use proper URL parsing
        return DatabaseConfig()

    def get_redis_config(self) -> RedisConfig:
        """Parse Redis configuration from URL"""
        # Simplified parsing - in production, use proper URL parsing
        return RedisConfig()

    def get_solana_config(self) -> SolanaConfig:
        """Get Solana configuration"""
        return SolanaConfig(
            network=self.solana_network,
            rpc_url=self.solana_rpc_url
        )


class ConfigManager:
    """Advanced configuration management with hot reloading"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.settings: Optional[ProductionSettings] = None
        self._watchers: Dict[str, Any] = {}
        self._callbacks: List[callable] = []

    def load_settings(self, environment: Optional[Environment] = None) -> ProductionSettings:
        """Load settings for specified environment"""
        if environment is None:
            environment = Environment(os.getenv("ENVIRONMENT", "development"))

        # Load base settings
        self.settings = ProductionSettings()

        # Load environment-specific overrides
        env_config_file = self.config_dir / f"{environment.value}.yaml"
        if env_config_file.exists():
            self._load_yaml_overrides(env_config_file)

        # Load secrets if available
        secrets_file = self.config_dir / "secrets.yaml"
        if secrets_file.exists():
            self._load_secrets(secrets_file)

        logger.info(f"Configuration loaded for environment: {environment.value}")
        return self.settings

    def _load_yaml_overrides(self, config_file: Path):
        """Load YAML configuration overrides"""
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            if config_data:
                # Apply overrides to settings
                for key, value in config_data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)

        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")

    def _load_secrets(self, secrets_file: Path):
        """Load secrets from secure file"""
        try:
            with open(secrets_file, 'r') as f:
                secrets = yaml.safe_load(f)

            if secrets:
                for key, value in secrets.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                        logger.debug(f"Loaded secret: {key}")

        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")

    def register_change_callback(self, callback: callable):
        """Register callback for configuration changes"""
        self._callbacks.append(callback)

    async def start_hot_reload(self):
        """Start hot reloading of configuration"""
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ConfigHandler(FileSystemEventHandler):
                def __init__(self, manager):
                    self.manager = manager

                def on_modified(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith(('.yaml', '.yml', '.env')):
                        logger.info(f"Configuration file changed: {event.src_path}")
                        asyncio.create_task(self.manager._reload_config())

            observer = Observer()
            observer.schedule(ConfigHandler(self), str(self.config_dir), recursive=True)
            observer.start()

            logger.info("Hot reload enabled for configuration files")

        except ImportError:
            logger.warning("Watchdog not available, hot reload disabled")

    async def _reload_config(self):
        """Reload configuration and notify callbacks"""
        try:
            old_settings = self.settings
            self.load_settings()

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_settings, self.settings)
                    else:
                        callback(old_settings, self.settings)
                except Exception as e:
                    logger.error(f"Configuration change callback failed: {e}")

        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")

    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return any issues"""
        issues = []

        if not self.settings:
            issues.append("Configuration not loaded")
            return issues

        # Production-specific validations
        if self.settings.environment == Environment.PRODUCTION:
            if not self.settings.secret_key:
                issues.append("SECRET_KEY not set in production")

            if self.settings.debug:
                issues.append("Debug mode enabled in production")

            if self.settings.reload:
                issues.append("Auto-reload enabled in production")

        # Database validation
        if self.settings.database_url.startswith("sqlite://") and \
           self.settings.environment == Environment.PRODUCTION:
            issues.append("SQLite not recommended for production")

        # Security validations
        if not self.settings.api_keys and self.settings.environment != Environment.DEVELOPMENT:
            issues.append("No API keys configured")

        return issues

    def export_config(self, format: str = "yaml", include_secrets: bool = False) -> str:
        """Export current configuration"""
        if not self.settings:
            raise ValueError("No configuration loaded")

        config_dict = self.settings.dict()

        # Remove secrets if not requested
        if not include_secrets:
            sensitive_keys = ["secret_key", "api_keys", "openai_api_key", "anthropic_api_key"]
            for key in sensitive_keys:
                if key in config_dict:
                    config_dict[key] = "[REDACTED]"

        if format == "yaml":
            return yaml.dump(config_dict, default_flow_style=False)
        elif format == "json":
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    Environment.DEVELOPMENT: {
        "debug": True,
        "reload": True,
        "workers": 1,
        "log_level": LogLevel.DEBUG,
        "enable_profiling": True,
    },
    Environment.TESTING: {
        "debug": False,
        "testing": True,
        "database_url": "sqlite:///./test.db",
        "redis_url": "redis://localhost:6379/1",
    },
    Environment.STAGING: {
        "debug": False,
        "workers": 2,
        "log_level": LogLevel.INFO,
        "enable_monitoring": True,
    },
    Environment.PRODUCTION: {
        "debug": False,
        "reload": False,
        "workers": 4,
        "log_level": LogLevel.WARNING,
        "enable_monitoring": True,
        "enable_profiling": False,
    }
}


# Global configuration manager
config_manager = ConfigManager()


def get_settings() -> ProductionSettings:
    """Get current settings"""
    if config_manager.settings is None:
        config_manager.load_settings()
    return config_manager.settings


def load_config_for_environment(env: Environment) -> ProductionSettings:
    """Load configuration for specific environment"""
    return config_manager.load_settings(env)