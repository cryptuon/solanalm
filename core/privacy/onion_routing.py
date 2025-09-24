"""
Tor-like Onion Routing for Private LLM Inference

Implements multi-hop encrypted routing to hide request origin, destination,
and content from intermediate nodes - like Tor but for AI inference.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import base64
import secrets
import time

from core.models.schemas import NodeCapabilities, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class OnionLayer:
    """Single layer of onion encryption"""
    node_id: str
    node_public_key: bytes
    encrypted_payload: bytes
    next_hop: Optional[str] = None


@dataclass
class Circuit:
    """Complete onion routing circuit"""
    circuit_id: str
    path: List[str]  # Node IDs in order
    symmetric_keys: List[bytes]  # Shared keys with each node
    created_at: float
    expires_at: float


class OnionRouter:
    """Handles onion routing for private inference"""

    def __init__(self, min_hops: int = 3, max_hops: int = 5):
        self.min_hops = min_hops
        self.max_hops = max_hops
        self.circuits: Dict[str, Circuit] = {}
        self.node_keys: Dict[str, bytes] = {}  # Node public keys

        # Generate our own key pair for circuit establishment
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def register_node_key(self, node_id: str, public_key_pem: bytes):
        """Register a node's public key for encryption"""
        self.node_keys[node_id] = public_key_pem

    async def build_circuit(
        self,
        available_nodes: List[NodeCapabilities],
        target_model: str,
        exclude_countries: Optional[List[str]] = None
    ) -> Optional[Circuit]:
        """
        Build an onion routing circuit for private inference

        Like Tor, we select a path through multiple nodes:
        - Entry node: First hop, knows your IP but not destination
        - Middle nodes: Relay traffic, know neither source nor destination
        - Exit node: Final hop, performs inference but doesn't know source
        """

        # Filter nodes that support the target model
        suitable_nodes = [
            node for node in available_nodes
            if target_model in node.supported_models
            and node.node_id in self.node_keys
        ]

        if len(suitable_nodes) < self.min_hops:
            logger.warning(f"Not enough nodes for circuit: {len(suitable_nodes)} < {self.min_hops}")
            return None

        # Select diverse path (different geographical regions if possible)
        path = self._select_diverse_path(suitable_nodes, exclude_countries)

        if not path:
            return None

        # Establish circuit by creating shared keys with each node
        circuit_id = secrets.token_hex(16)
        symmetric_keys = []

        for i, node_id in enumerate(path):
            try:
                # Generate shared symmetric key for this hop
                symmetric_key = secrets.token_bytes(32)  # 256-bit AES key
                symmetric_keys.append(symmetric_key)

                # TODO: In production, use Diffie-Hellman key exchange
                # For now, simulate establishing keys
                logger.debug(f"Established key with node {node_id} (hop {i+1})")

            except Exception as e:
                logger.error(f"Failed to establish circuit at hop {i+1}: {e}")
                return None

        circuit = Circuit(
            circuit_id=circuit_id,
            path=path,
            symmetric_keys=symmetric_keys,
            created_at=time.time(),
            expires_at=time.time() + 3600  # 1 hour circuit lifetime
        )

        self.circuits[circuit_id] = circuit

        logger.info(f"Built circuit {circuit_id} with {len(path)} hops: {' -> '.join(path)}")
        return circuit

    def _select_diverse_path(
        self,
        nodes: List[NodeCapabilities],
        exclude_countries: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """
        Select a diverse path through the network

        Enhanced privacy-preserving node selection:
        - Choose nodes from different operators/regions
        - Avoid nodes in excluded countries
        - Prefer high-reputation nodes
        - Ensure geographic diversity
        - Avoid potential correlation attacks
        - Balance security vs performance
        """

        if len(nodes) < self.min_hops:
            return None

        # Enhanced node filtering and scoring
        suitable_nodes = self._filter_nodes_for_privacy(nodes, exclude_countries)

        if len(suitable_nodes) < self.min_hops:
            logger.warning(f"Insufficient nodes after privacy filtering: {len(suitable_nodes)}")
            return None

        # Select path with maximum diversity
        path = self._select_optimal_privacy_path(suitable_nodes)

        if len(path) < self.min_hops:
            # Fallback: relaxed selection
            path = self._fallback_path_selection(suitable_nodes)

        return path

    def _filter_nodes_for_privacy(
        self,
        nodes: List[NodeCapabilities],
        exclude_countries: Optional[List[str]] = None
    ) -> List[NodeCapabilities]:
        """Filter nodes based on privacy criteria"""

        filtered_nodes = []

        for node in nodes:
            # Basic availability check
            if node.status.value != "online":
                continue

            # Reputation threshold for privacy
            if node.reputation_score < 0.7:  # Higher threshold for privacy
                continue

            # Exclude known bad actors (mock implementation)
            if self._is_potential_bad_actor(node):
                continue

            # Geographic exclusions
            if exclude_countries and self._get_node_country(node) in exclude_countries:
                continue

            # Avoid nodes with suspicious patterns
            if self._has_suspicious_patterns(node):
                continue

            filtered_nodes.append(node)

        return filtered_nodes

    def _select_optimal_privacy_path(self, nodes: List[NodeCapabilities]) -> List[str]:
        """Select optimal path for privacy using advanced algorithms"""

        # Score nodes based on multiple privacy factors
        scored_nodes = []
        for node in nodes:
            privacy_score = self._calculate_privacy_score(node)
            scored_nodes.append((privacy_score, node))

        # Sort by privacy score
        scored_nodes.sort(key=lambda x: x[0], reverse=True)

        # Greedy selection with diversity constraints
        path = []
        used_operators = set()
        used_countries = set()
        used_asns = set()  # Autonomous System Numbers for network diversity

        for privacy_score, node in scored_nodes:
            if len(path) >= self.max_hops:
                break

            # Diversity checks
            operator = self._get_node_operator(node)
            country = self._get_node_country(node)
            asn = self._get_node_asn(node)

            # Ensure diversity
            if (operator not in used_operators and
                country not in used_countries and
                asn not in used_asns):

                path.append(node.node_id)
                used_operators.add(operator)
                used_countries.add(country)
                used_asns.add(asn)

        return path

    def _calculate_privacy_score(self, node: NodeCapabilities) -> float:
        """Calculate privacy score for node selection"""

        score = 0.0

        # Base reputation (30% weight)
        score += node.reputation_score * 30

        # Uptime history (20% weight)
        uptime_score = min(node.success_rate, 1.0) * 20
        score += uptime_score

        # Geographic diversity bonus (15% weight)
        country = self._get_node_country(node)
        if country in ["CH", "SE", "IS", "NL"]:  # Privacy-friendly countries
            score += 15
        elif country in ["CN", "RU", "IR", "KP"]:  # Authoritarian countries
            score -= 15

        # Operator diversity (10% weight)
        if self._is_independent_operator(node):
            score += 10

        # Network performance (15% weight)
        if node.average_response_time < 2.0:  # Fast responses
            score += 15
        elif node.average_response_time > 5.0:  # Slow responses
            score -= 5

        # Privacy features (10% weight)
        if hasattr(node, 'supports_onion_routing'):
            score += 10

        return score

    def _fallback_path_selection(self, nodes: List[NodeCapabilities]) -> List[str]:
        """Fallback path selection with relaxed constraints"""

        # Just ensure basic operator diversity
        path = []
        used_operators = set()

        nodes_by_reputation = sorted(nodes, key=lambda n: n.reputation_score, reverse=True)

        for node in nodes_by_reputation:
            if len(path) >= self.max_hops:
                break

            operator = self._get_node_operator(node)
            if operator not in used_operators:
                path.append(node.node_id)
                used_operators.add(operator)

        # If still not enough, add remaining high-reputation nodes
        if len(path) < self.min_hops:
            for node in nodes_by_reputation:
                if len(path) >= self.min_hops:
                    break
                if node.node_id not in path:
                    path.append(node.node_id)

        return path

    def _get_node_operator(self, node: NodeCapabilities) -> str:
        """Get node operator identifier"""
        return node.wallet_address[:10]  # First 10 chars as operator ID

    def _get_node_country(self, node: NodeCapabilities) -> str:
        """Get node country (mock implementation)"""
        # In production, this would use GeoIP or node-provided location
        import hashlib
        country_hash = hashlib.md5(node.node_id.encode()).hexdigest()[:2]
        country_map = {
            "00": "US", "01": "DE", "02": "GB", "03": "FR", "04": "CA",
            "05": "JP", "06": "AU", "07": "CH", "08": "SE", "09": "NL",
            "10": "SG", "11": "KR", "12": "BR", "13": "IN", "14": "MX",
            "15": "ES", "16": "IT", "17": "BE", "18": "AT", "19": "NO"
        }
        return country_map.get(country_hash[:2], "XX")

    def _get_node_asn(self, node: NodeCapabilities) -> str:
        """Get node Autonomous System Number (mock implementation)"""
        import hashlib
        asn_hash = hashlib.md5(f"asn-{node.node_id}".encode()).hexdigest()[:4]
        return f"AS{int(asn_hash, 16) % 70000}"

    def _is_independent_operator(self, node: NodeCapabilities) -> bool:
        """Check if node is run by independent operator"""
        # Mock implementation - in production, would check operator database
        return not any(corp in node.wallet_address.lower() for corp in ['aws', 'google', 'microsoft', 'cloudflare'])

    def _is_potential_bad_actor(self, node: NodeCapabilities) -> bool:
        """Check for potential bad actors (mock implementation)"""
        # In production, would check against known bad actor lists
        return (
            node.reputation_score < 0.3 or
            node.success_rate < 0.5 or
            node.total_requests_served < 10
        )

    def _has_suspicious_patterns(self, node: NodeCapabilities) -> bool:
        """Check for suspicious behavioral patterns"""
        # Mock implementation - in production would analyze traffic patterns
        return (
            # Too new with high reputation (possible Sybil)
            node.total_requests_served < 100 and node.reputation_score > 0.95 or
            # Suspiciously perfect metrics
            node.success_rate == 1.0 and node.total_requests_served > 1000
        )

    async def route_request(
        self,
        circuit: Circuit,
        request: InferenceRequest
    ) -> bytes:
        """
        Route request through onion circuit

        Like Tor:
        1. Encrypt payload for exit node
        2. Add layer for each middle node (working backwards)
        3. Send to entry node with multiple encryption layers
        """

        # Start with the actual inference request
        payload = {
            "type": "inference_request",
            "model": request.model,
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "metadata": request.metadata or {}
        }

        current_payload = json.dumps(payload).encode()

        # Apply onion encryption (work backwards through the circuit)
        for i in reversed(range(len(circuit.path))):
            node_id = circuit.path[i]
            symmetric_key = circuit.symmetric_keys[i]

            # Encrypt this layer
            f = Fernet(base64.urlsafe_b64encode(symmetric_key))
            current_payload = f.encrypt(current_payload)

            # Add routing header for this hop
            if i > 0:  # Not the last hop
                next_hop = circuit.path[i-1]  # Previous in path (we're working backwards)
                routing_header = {
                    "type": "onion_forward",
                    "circuit_id": circuit.circuit_id,
                    "next_hop": next_hop,
                    "payload": base64.b64encode(current_payload).decode()
                }
            else:  # First hop (entry node)
                routing_header = {
                    "type": "onion_start",
                    "circuit_id": circuit.circuit_id,
                    "payload": base64.b64encode(current_payload).decode()
                }

            current_payload = json.dumps(routing_header).encode()

        return current_payload

    async def send_through_circuit(
        self,
        circuit: Circuit,
        request: InferenceRequest,
        entry_node_url: str
    ) -> Any:
        """Send request through the onion circuit"""

        try:
            # Create onion-encrypted payload
            onion_payload = await self.route_request(circuit, request)

            # Send to entry node
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{entry_node_url}/onion_route",
                    data=onion_payload,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=60  # Longer timeout for multi-hop
                ) as response:
                    if response.status == 200:
                        # Response comes back through the same circuit (encrypted)
                        encrypted_response = await response.read()
                        return await self._decrypt_response(circuit, encrypted_response)
                    else:
                        raise Exception(f"Circuit routing failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send through circuit {circuit.circuit_id}: {e}")
            raise

    async def _decrypt_response(self, circuit: Circuit, encrypted_response: bytes) -> Any:
        """Decrypt response coming back through circuit"""

        current_data = encrypted_response

        # Decrypt each layer (in forward order this time)
        for i in range(len(circuit.symmetric_keys)):
            symmetric_key = circuit.symmetric_keys[i]
            f = Fernet(base64.urlsafe_b64encode(symmetric_key))
            current_data = f.decrypt(current_data)

        # Parse final response
        response_data = json.loads(current_data.decode())
        return response_data

    def cleanup_expired_circuits(self):
        """Remove expired circuits"""
        current_time = time.time()
        expired = [
            circuit_id for circuit_id, circuit in self.circuits.items()
            if circuit.expires_at < current_time
        ]

        for circuit_id in expired:
            del self.circuits[circuit_id]
            logger.debug(f"Cleaned up expired circuit {circuit_id}")


class PrivateInferenceGateway:
    """Gateway that provides Tor-like private inference"""

    def __init__(self, node_registry):
        self.node_registry = node_registry
        self.onion_router = OnionRouter()

    async def private_inference(
        self,
        request: InferenceRequest,
        privacy_level: str = "standard"  # "standard", "high", "maximum"
    ) -> Any:
        """
        Perform private inference using onion routing

        Privacy levels:
        - standard: 3 hops, basic geographic diversity
        - high: 4-5 hops, strict geographic diversity
        - maximum: 5+ hops, additional delays, country exclusions
        """

        # Configure based on privacy level
        if privacy_level == "high":
            self.onion_router.min_hops = 4
            exclude_countries = ["CN", "RU", "IR", "KP"]  # Example exclusions
        elif privacy_level == "maximum":
            self.onion_router.min_hops = 5
            exclude_countries = ["CN", "RU", "IR", "KP", "US", "UK"]
            # Add random delays to frustrate timing analysis
            await asyncio.sleep(secrets.randbelow(5))
        else:
            exclude_countries = None

        # Get available nodes
        available_nodes = await self.node_registry.get_all_nodes()

        # Build circuit
        circuit = await self.onion_router.build_circuit(
            available_nodes,
            request.model,
            exclude_countries
        )

        if not circuit:
            raise Exception("Could not build private circuit - insufficient nodes")

        # Get entry node URL
        entry_node = next(
            node for node in available_nodes
            if node.node_id == circuit.path[0]
        )

        try:
            # Route request through circuit
            response = await self.onion_router.send_through_circuit(
                circuit, request, entry_node.endpoint_url
            )

            return response

        finally:
            # Circuit is single-use for maximum privacy
            if circuit.circuit_id in self.onion_router.circuits:
                del self.onion_router.circuits[circuit.circuit_id]


# Example usage and testing
async def test_private_inference():
    """Test the private inference system"""

    print("🕵️ Testing Tor-like Private Inference")
    print("=" * 40)

    # Mock setup
    from unittest.mock import AsyncMock

    mock_registry = AsyncMock()

    # Create mock nodes
    mock_nodes = []
    for i in range(5):
        node = NodeCapabilities(
            node_id=f"node-{i}",
            node_type="inference",
            wallet_address=f"wallet-{i}",
            endpoint_url=f"http://node-{i}:8100",
            hardware=None,
            pricing=None,
            supported_models=["gpt-3.5-turbo", "claude-haiku"]
        )
        mock_nodes.append(node)

    mock_registry.get_all_nodes.return_value = mock_nodes

    # Test private gateway
    gateway = PrivateInferenceGateway(mock_registry)

    # Register mock node keys
    for node in mock_nodes:
        mock_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        gateway.onion_router.register_node_key(
            node.node_id,
            mock_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    # Test circuit building
    circuit = await gateway.onion_router.build_circuit(
        mock_nodes, "gpt-3.5-turbo"
    )

    if circuit:
        print(f"✅ Built circuit with {len(circuit.path)} hops")
        print(f"   Path: {' -> '.join(circuit.path)}")
        print(f"   Circuit ID: {circuit.circuit_id}")
    else:
        print("❌ Failed to build circuit")

    print("\n🔒 Privacy Benefits:")
    print("- Entry node knows your IP but not what you're asking")
    print("- Middle nodes know neither source nor destination")
    print("- Exit node processes request but doesn't know who asked")
    print("- Each request uses a new circuit for maximum privacy")
    print("- Multi-layer encryption protects content at each hop")


if __name__ == "__main__":
    asyncio.run(test_private_inference())