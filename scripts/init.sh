#!/bin/bash

# SolanaLM Initialization Script (Revised)

echo "Initializing SolanaLM Project..."

# Create necessary directories
echo "Creating directory structure..."
mkdir -p config
mkdir -p data
mkdir -p models
mkdir -p logs

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize Solana configuration
echo "Setting up Solana configuration..."
if ! command -v solana &> /dev/null
then
    echo "Solana CLI not found. Please install it first:"
    echo "sh -c \"$(curl -sSfL https://release.solana.com/stable/install)\""
    exit 1
fi

# Create default configuration files
echo "Creating default configuration files..."

cat > config/trainer.yaml << EOF
# Trainer Node Configuration
node:
  id: "trainer-001"
  name: "Default Trainer Node"
  
# Network Configuration
network:
  solana_rpc: "https://api.devnet.solana.com"
  coordinator_url: "http://localhost:8001"
  
# Hardware Configuration
hardware:
  gpu_required: true
  min_vram_gb: 16
  min_ram_gb: 32
  
# Data Configuration
data:
  providers:
    - type: "wikitext"
      path: "./data/wikitext"
    - type: "synthetic"
      config:
        domain: "general"
        
# Model Configuration
model:
  default_adapter: "qwen-slm"
  training_method: "lora"
  
# Storage Configuration
storage:
  cache_dir: "./models/cache"
  
# Logging Configuration
logging:
  level: "INFO"
  file: "./logs/trainer.log"
EOF

cat > config/coordinator.yaml << EOF
# Coordinator Configuration
coordinator:
  id: "coordinator-001"
  name: "Default Coordinator"
  
# Network Configuration
network:
  solana_rpc: "https://api.devnet.solana.com"
  bind_address: "0.0.0.0"
  port: 8001
  
# Database Configuration
database:
  url: "postgresql://solanalm:solanalm@localhost:5432/solanalm"
  
# Storage Configuration
storage:
  cache_dir: "./models/cache"
  
# Logging Configuration
logging:
  level: "INFO"
  file: "./logs/coordinator.log"
  
# Round Configuration
rounds:
  default_duration_minutes: 30
  min_participants: 5
  max_participants: 100
EOF

cat > config/inference.yaml << EOF
# Inference Server Configuration
inference:
  id: "inference-001"
  name: "Default Inference Server"
  
# API Configuration
api:
  bind_address: "0.0.0.0"
  port: 8000
  cors_origins:
    - "*"
  
# Model Configuration
models:
  cache_size_gb: 10
  max_concurrent_models: 5
  
# Storage Configuration
storage:
  cache_dir: "./models/cache"
  
# Authentication Configuration
auth:
  enabled: false  # Set to true for production
  
# Rate Limiting Configuration
rate_limiting:
  enabled: true
  requests_per_minute: 60
  
# Logging Configuration
logging:
  level: "INFO"
  file: "./logs/inference.log"
EOF

echo "Configuration files created successfully!"

# Initialize Git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Project structure and configuration"
fi

echo "SolanaLM project initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Review and update configuration files in the config/ directory"
echo "2. For development, run 'docker-compose up' to start all services"
echo "3. For training, run 'python core/trainer/node.py --config config/trainer.yaml'"
echo "4. For coordination, run 'python core/coordinator/server.py --config config/coordinator.yaml'"
echo "5. For inference, run 'python core/inference/server.py --config config/inference.yaml'"