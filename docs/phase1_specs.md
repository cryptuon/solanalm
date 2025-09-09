# Phase 1 Technical Specifications

## Overview

Phase 1 focuses on building the core infrastructure of the SolanaLM network, including the Solana smart contracts, basic training framework, and a minimum viable network for testing.

## Solana Programs

### Training Coordinator Program

#### Program ID
`TCoorD1nateR9tRainingJobsAndParticipants1111`

#### Accounts
- `TrainingJob`: Stores job metadata and state
- `Participant`: Tracks registered trainer nodes
- `Round`: Manages training round information
- `Escrow`: Handles payment escrow for jobs

#### Instructions
- `initialize_job`: Creates a new training job
  - Parameters: model spec, data requirements, reward pool
  - Accounts: job account, coordinator wallet, escrow account
- `register_participant`: Registers a trainer node for a job
  - Parameters: node info, capabilities
  - Accounts: job account, participant account, node wallet
- `submit_gradient`: Submits gradient updates for a round
  - Parameters: round ID, gradient hash, proof of training
  - Accounts: job account, round account, participant account
- `complete_round`: Aggregates gradients and completes round
  - Parameters: aggregated gradients, proof
  - Accounts: job account, round account, coordinator wallet
- `distribute_rewards`: Distributes rewards to participants
  - Parameters: reward amounts, proof of contribution
  - Accounts: job account, escrow, participant wallets

#### State Management
- Jobs progress through states: Initializing → Active → Paused → Completed
- Rounds track participant submissions and aggregation status
- Participants maintain reputation scores

### Token Economics Program

#### Program ID
`TokeNecoNom1csForTrainingAndData1111111`

#### Accounts
- `TokenPool`: Manages token distribution and rewards
- `StakeAccount`: Tracks staked tokens for participants
- `RewardsLedger`: Records reward distributions

#### Instructions
- `initialize_pool`: Sets up a new token pool
- `stake_tokens`: Allows participants to stake tokens
- `claim_rewards`: Enables claiming of earned rewards
- `slash_stake`: Reduces stake for poor performance

#### Token Types
- `$SLMNET`: Governance and staking token
- `$COMPUTE`: Earned by GPU providers
- `$DATA`: Earned by data providers

### Model Registry Program

#### Program ID
`ModeLreg1stryForTrackedModels111111111`

#### Accounts
- `Model`: Stores model metadata and version info
- `Benchmark`: Tracks model performance metrics
- `License`: Manages model access rights

#### Instructions
- `register_model`: Registers a new model
- `update_benchmark`: Updates model performance metrics
- `grant_license`: Grants access to a model
- `revoke_license`: Revokes access to a model

## Training Framework

### Core Trainer Node

#### Components
- **Model Loader**: Loads and initializes models based on job requirements
- **Training Executor**: Runs training using specified backend
- **Gradient Handler**: Compresses and encrypts gradient updates
- **Network Client**: Communicates with coordinator and other nodes
- **Wallet Manager**: Handles Solana wallet operations

#### Configuration
```yaml
node:
  id: "trainer-001"
  capabilities:
    gpu: "RTX4090"
    memory: "64GB"
    bandwidth: "1Gbps"
  wallet: "solana_wallet_address"
  data_sources: []
```

### FedML Integration

#### Features
- Round-based federated learning coordination
- Gradient aggregation using FedAvg
- Support for reputation-weighted averaging
- Integration with Solana transaction system

#### Communication Flow
1. Coordinator initializes training round
2. Nodes download latest model weights
3. Nodes perform local training
4. Nodes compress and encrypt gradients
5. Nodes submit gradients to coordinator
6. Coordinator aggregates gradients
7. Coordinator updates global model
8. Coordinator distributes rewards

### Gradient Compression Pipeline

#### Stages
1. **Mixed Precision Training**: Use bf16 for reduced memory
2. **Quantization**: Convert to int8 with error correction
3. **Sparsification**: Keep top 10% of gradients (TopK)
4. **Delta Compression**: Compress against previous round
5. **Encryption**: AES encryption before transmission

#### Implementation
- Custom PyTorch modules for each stage
- Configurable compression ratios
- Error tracking and correction mechanisms

## Network Infrastructure

### Minimum Viable Network

#### Trainer Nodes
- 20 beta testers with varying hardware:
  - 10 nodes: RTX 4090, 64GB RAM (recommended)
  - 10 nodes: RTX 4060 Ti, 32GB RAM (minimum)

#### Specialized SLMs
1. **Code Model**: Specialized for programming tasks
2. **Documentation Model**: Optimized for technical documentation
3. **Chat Model**: Fine-tuned for conversational AI
4. **Math Model**: Specialized for mathematical reasoning
5. **Writing Model**: Optimized for creative writing

#### Basic Solana Integration
- Wallet management for all participants
- Automatic reward distribution
- On-chain tracking of training progress
- Basic reputation scoring

## Testing and Validation

### Unit Tests
- Smart contract instruction tests
- Model loading and gradient computation
- Compression and encryption algorithms
- Network communication protocols

### Integration Tests
- End-to-end training job flow
- Reward distribution mechanisms
- Model registry operations
- Cross-program interactions

### Performance Benchmarks
- Transaction throughput for coordinator operations
- Gradient compression/decompression speed
- Model loading and initialization time
- Network latency for gradient submission

## Success Criteria

### Technical
- All three Solana programs deployed and functional
- Training framework supports basic FedML operations
- Gradient compression reduces data size by 90%+
- Network can coordinate 20+ nodes in parallel

### Operational
- Beta testers can successfully run training jobs
- Rewards are distributed correctly
- Model performance is tracked on-chain
- System achieves 95%+ uptime during testing

### Documentation
- Smart contract APIs documented
- Training framework usage guide
- Deployment instructions for trainer nodes
- Troubleshooting guide for common issues