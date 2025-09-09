# Distributed Inference for SolanaLM

## Overview

This document specifies the distributed inference capability for SolanaLM Phase 1, allowing model owners to distribute inference workloads across multiple nodes in the network when permitted by the weight developer/model owner.

## Distributed Inference Architecture

### Core Concept

Instead of requiring all inference to happen on a single node, SolanaLM enables model owners to:
1. **Distribute inference workloads** across multiple nodes in the network
2. **Maintain control** over who can serve their models
3. **Earn rewards** for nodes that participate in serving inference requests
4. **Scale inference capacity** based on demand

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Model Owner   │    │  Coordinator     │    │  Inference       │
│  (Permission    │    │  (Solana)        │    │  Requestor       │
│  Grantor)       │    │                  │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Model          │    │  Inference       │    │  Inference       │
│  Permissions    │◄──►│  Routing         │◄──►│  Request         │
└─────────────────┘    │  (Load Balancing)│    └──────────────────┘
         │             └──────────────────┘              │
         ▼                       │                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Solana         │    │  Distributed     │    │  Request         │
│  Program        │◄──►│  Inference       │◄──►│  Distribution    │
│  (Access Ctrl)  │    │  Network         │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         ▲                       │                        ▲
         │                       ▼                        │
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Inference      │    │  Model Replica   │    │  Response        │
│  Node           │    │  Nodes           │    │  Aggregation     │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## Implementation Details

### 1. Permission System

Model owners can specify inference distribution permissions:

```python
class InferencePermissions:
    def __init__(self):
        self.distributed_inference_allowed = False
        self.authorized_nodes = []  # List of allowed node IDs
        self.max_concurrent_requests = 100
        self.rate_limits = {
            "requests_per_minute": 1000,
            "tokens_per_minute": 100000
        }
        self.reward_sharing = 0.7  # 70% of inference fees shared with serving nodes
```

### 2. Inference Node Registration

Nodes that want to serve inference requests must register:

```python
class InferenceNode:
    def __init__(self, node_id, capabilities):
        self.node_id = node_id
        self.capabilities = capabilities  # GPU type, memory, etc.
        self.registered_models = {}  # Models this node can serve
        
    def register_for_inference(self, model_id, permissions):
        """Register to serve inference for a model"""
        # Verify permissions from Solana
        # Add to registered models list
        # Update Solana program with node info
        pass
```

### 3. Distributed Inference Coordinator

The coordinator manages distributed inference requests:

```python
class DistributedInferenceCoordinator:
    def __init__(self, solana_client):
        self.solana_client = solana_client
        self.node_registry = {}
        self.load_balancer = LoadBalancer()
        
    def route_inference_request(self, model_id, request):
        """Route inference request to appropriate nodes"""
        # Get model permissions
        permissions = self._get_model_permissions(model_id)
        
        # Check if distributed inference is allowed
        if not permissions.distributed_inference_allowed:
            # Route to model owner's node
            return self._route_to_owner(model_id, request)
        
        # Get available nodes for this model
        available_nodes = self._get_authorized_nodes(model_id)
        
        # Load balance across nodes
        selected_nodes = self.load_balancer.select_nodes(
            available_nodes, 
            request.complexity
        )
        
        # Distribute request if it's a batch that can be split
        if self._can_distribute_request(request) and len(selected_nodes) > 1:
            return self._distribute_request(selected_nodes, request)
        else:
            # Route to single node
            return self._route_to_single_node(selected_nodes[0], request)
    
    def _distribute_request(self, nodes, request):
        """Distribute a large inference request across multiple nodes"""
        # Split request into sub-requests
        sub_requests = self._split_request(request, len(nodes))
        
        # Send sub-requests to nodes
        responses = []
        for i, node in enumerate(nodes):
            response = node.process_inference(sub_requests[i])
            responses.append(response)
        
        # Aggregate responses
        return self._aggregate_responses(responses)
```

### 4. Solana Program Updates

The Model Registry program needs updates to handle inference permissions:

```rust
// Updated Model account structure
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
pub struct InferencePermissions {
    pub distributed_inference_allowed: bool,
    pub authorized_nodes: Vec<Pubkey>,
    pub max_concurrent_requests: u32,
    pub rate_limits: RateLimits,
    pub reward_sharing_percentage: u8,  // 0-100
}

// New instructions
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

### 5. Request Distribution and Aggregation

For large batch requests, the system can distribute work:

```python
class RequestDistributor:
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
```

## Benefits of Distributed Inference

### 1. Scalability
- **Horizontal Scaling**: Add more nodes to handle increased load
- **Load Distribution**: Spread inference work across multiple nodes
- **Peak Handling**: Handle traffic spikes without performance degradation

### 2. Performance
- **Reduced Latency**: Parallel processing of large batches
- **Increased Throughput**: More requests processed per second
- **Geographic Distribution**: Serve requests from closer nodes

### 3. Economic Incentives
- **Revenue Sharing**: Model owners can share inference revenue with serving nodes
- **Market for Compute**: Nodes can earn rewards for serving inference
- **Resource Optimization**: Better utilization of network compute resources

### 4. Reliability
- **Fault Tolerance**: Failure of one node doesn't stop inference
- **Redundancy**: Multiple nodes can serve the same model
- **High Availability**: 24/7 inference availability

## Implementation Plan

### Phase 1 Integration
1. **Extend Model Registry Program** with inference permissions
2. **Add Inference Node Registration** functionality
3. **Implement Basic Request Routing** to authorized nodes
4. **Create Reward Distribution** mechanism

### Phase 2 Enhancement
1. **Implement Request Distribution** for large batches
2. **Add Load Balancing** algorithms
3. **Implement Response Aggregation** for distributed requests
4. **Add Monitoring and Metrics** for distributed inference

## Security Considerations

### 1. Access Control
- Only model owners can grant inference permissions
- Authorization verified through Solana programs
- Regular permission validation

### 2. Data Privacy
- Input data encrypted in transit
- No storage of inference inputs on serving nodes
- Secure aggregation of distributed responses

### 3. Economic Security
- Prevention of reward theft
- Verification of inference work performed
- Slashing conditions for malicious nodes

## Cost Model

### For Model Owners
- **Infrastructure Savings**: No need to maintain large inference clusters
- **Revenue Sharing**: Share a percentage of inference fees (e.g., 70%)
- **Scalability**: Pay only for actual usage

### For Inference Providers
- **Earning Opportunity**: Earn rewards for serving inference
- **Low Investment**: Use existing hardware
- **Flexible Participation**: Opt-in to serve specific models

### For Requestors
- **Same API**: No changes to existing inference requests
- **Better Performance**: Faster responses for large batches
- **Reliability**: Higher availability and fault tolerance

## Example Usage

### Model Owner Enabling Distributed Inference
```python
# Model owner grants permission for distributed inference
permissions = InferencePermissions()
permissions.distributed_inference_allowed = True
permissions.reward_sharing_percentage = 70  # Share 70% of fees
permissions.max_concurrent_requests = 1000

# Set permissions on Solana
solana_interface.set_inference_permissions(model_id, permissions)
```

### Inference Node Registration
```python
# Node registers to serve inference
node = InferenceNode(node_id="node-123", capabilities={"gpu": "RTX4090", "memory": "64GB"})
node.register_for_inference(model_id, permissions)
```

### Distributed Inference Request
```python
# Large batch request that gets distributed
request = InferenceRequest(
    model_id="my-model",
    inputs=large_batch_of_inputs,  # 1000 items
    batch_size=1000
)

# Coordinator automatically distributes the request
response = inference_coordinator.process_request(request)
# Response is automatically aggregated from multiple nodes
```

This distributed inference capability enables SolanaLM to scale inference workloads while maintaining model owner control and providing economic incentives for network participants.