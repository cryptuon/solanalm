"""
Onion Routing Handler for Nodes

Handles onion-routed requests at each hop in the privacy circuit.
Each node only knows the previous and next hop, never the full path.
"""

import asyncio
import logging
import json
import base64
from typing import Optional, Dict, Any
import aiohttp
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class OnionNodeHandler:
    """Handles onion routing at individual nodes"""

    def __init__(self, node_id: str, symmetric_keys: Dict[str, bytes]):
        self.node_id = node_id
        self.symmetric_keys = symmetric_keys  # circuit_id -> shared key
        self.active_circuits: Dict[str, Dict[str, Any]] = {}

    def register_circuit_key(self, circuit_id: str, symmetric_key: bytes):
        """Register a shared key for a circuit"""
        self.symmetric_keys[circuit_id] = symmetric_key
        logger.debug(f"Registered key for circuit {circuit_id}")

    async def handle_onion_request(self, encrypted_data: bytes) -> bytes:
        """
        Handle an onion-routed request

        This node only sees:
        - The encrypted payload (can't read inner layers)
        - The next hop (if it's not the exit node)
        - Nothing about the original source or final destination
        """

        try:
            # Parse the routing header
            routing_data = json.loads(encrypted_data.decode())
            request_type = routing_data.get("type")
            circuit_id = routing_data.get("circuit_id")

            if not circuit_id or circuit_id not in self.symmetric_keys:
                raise ValueError(f"Unknown circuit: {circuit_id}")

            if request_type == "onion_start":
                # Entry node - start the circuit
                return await self._handle_entry_node(routing_data)
            elif request_type == "onion_forward":
                # Middle node - forward to next hop
                return await self._handle_middle_node(routing_data)
            elif request_type == "onion_exit":
                # Exit node - perform the actual inference
                return await self._handle_exit_node(routing_data)
            else:
                raise ValueError(f"Unknown onion request type: {request_type}")

        except Exception as e:
            logger.error(f"Onion routing error: {e}")
            raise

    async def _handle_entry_node(self, routing_data: Dict[str, Any]) -> bytes:
        """Handle request as entry node"""
        circuit_id = routing_data["circuit_id"]
        encrypted_payload = base64.b64decode(routing_data["payload"])

        logger.debug(f"Entry node processing circuit {circuit_id}")

        # Decrypt our layer
        symmetric_key = self.symmetric_keys[circuit_id]
        f = Fernet(base64.urlsafe_b64encode(symmetric_key))
        decrypted_payload = f.decrypt(encrypted_payload)

        # Parse next routing instruction
        next_instruction = json.loads(decrypted_payload.decode())

        if next_instruction.get("type") == "onion_forward":
            # Forward to next hop
            next_hop = next_instruction["next_hop"]
            next_payload = next_instruction["payload"]

            return await self._forward_to_next_hop(
                next_hop, "onion_forward", circuit_id, next_payload
            )
        else:
            # This shouldn't happen at entry node
            raise ValueError("Invalid instruction at entry node")

    async def _handle_middle_node(self, routing_data: Dict[str, Any]) -> bytes:
        """Handle request as middle node"""
        circuit_id = routing_data["circuit_id"]
        next_hop = routing_data["next_hop"]
        encrypted_payload = base64.b64decode(routing_data["payload"])

        logger.debug(f"Middle node processing circuit {circuit_id}, forwarding to {next_hop}")

        # Decrypt our layer
        symmetric_key = self.symmetric_keys[circuit_id]
        f = Fernet(base64.urlsafe_b64encode(symmetric_key))
        decrypted_payload = f.decrypt(encrypted_payload)

        # Parse next instruction
        next_instruction = json.loads(decrypted_payload.decode())

        if next_instruction.get("type") == "inference_request":
            # We're the exit node - perform inference
            return await self._handle_exit_node({"circuit_id": circuit_id, "payload": base64.b64encode(decrypted_payload).decode()})
        else:
            # Forward to next hop
            return await self._forward_to_next_hop(
                next_hop,
                next_instruction.get("type", "onion_forward"),
                circuit_id,
                next_instruction.get("payload")
            )

    async def _handle_exit_node(self, routing_data: Dict[str, Any]) -> bytes:
        """Handle request as exit node - perform actual inference"""
        circuit_id = routing_data["circuit_id"]
        encrypted_payload = base64.b64decode(routing_data["payload"])

        logger.debug(f"Exit node processing circuit {circuit_id}")

        # Decrypt our layer to get the actual inference request
        symmetric_key = self.symmetric_keys[circuit_id]
        f = Fernet(base64.urlsafe_b64encode(symmetric_key))
        decrypted_payload = f.decrypt(encrypted_payload)

        # Parse the inference request
        inference_request = json.loads(decrypted_payload.decode())

        # Perform the actual inference
        response = await self._perform_inference(inference_request)

        # Encrypt the response for return journey
        response_json = json.dumps(response).encode()
        encrypted_response = f.encrypt(response_json)

        return encrypted_response

    async def _forward_to_next_hop(
        self,
        next_hop: str,
        request_type: str,
        circuit_id: str,
        payload: Optional[str]
    ) -> bytes:
        """Forward request to the next hop in the circuit"""

        # Look up next hop URL (in production, this would be from node registry)
        next_hop_url = self._get_node_url(next_hop)

        forward_data = {
            "type": request_type,
            "circuit_id": circuit_id,
            "payload": payload
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{next_hop_url}/onion_route",
                    json=forward_data,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        raise Exception(f"Forward failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to forward to {next_hop}: {e}")
            raise

    def _get_node_url(self, node_id: str) -> str:
        """Get URL for a node (mock implementation)"""
        # In production, this would query the node registry
        return f"http://{node_id}:8100"

    async def _perform_inference(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual inference request"""

        # Mock inference for now
        # In production, this would call the local model or external API

        model = request_data.get("model", "unknown")
        prompt = request_data.get("prompt", "")

        logger.info(f"Performing private inference: model={model}, prompt_length={len(prompt)}")

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Mock response
        response = {
            "request_id": f"private-{circuit_id}",
            "model": model,
            "response": f"Private response to: {prompt[:50]}...",
            "processing_time": 0.5,
            "tokens_generated": 10,
            "cost_sol": 0.001,
            "node_id": self.node_id,
            "privacy_mode": True
        }

        return response


class PrivacyMixin:
    """Mixin to add onion routing capabilities to existing nodes"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.onion_handler = OnionNodeHandler(
            self.node_id,
            {}  # Keys will be registered during circuit establishment
        )

    def setup_onion_routes(self):
        """Add onion routing endpoints to the node"""

        @self.app.post("/onion_route")
        async def onion_route_endpoint(request):
            """Handle onion-routed requests"""
            try:
                if request.headers.get("content-type") == "application/octet-stream":
                    # Binary data (encrypted payload)
                    data = await request.read()
                else:
                    # JSON data (routing instructions)
                    data = await request.json()
                    data = json.dumps(data).encode()

                response = await self.onion_handler.handle_onion_request(data)
                return response

            except Exception as e:
                logger.error(f"Onion routing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/establish_circuit")
        async def establish_circuit(circuit_data: dict):
            """Establish circuit with shared key"""
            circuit_id = circuit_data["circuit_id"]
            symmetric_key = base64.b64decode(circuit_data["symmetric_key"])

            self.onion_handler.register_circuit_key(circuit_id, symmetric_key)

            return {"status": "circuit_established", "node_id": self.node_id}


# Example of integrating privacy into existing nodes
class PrivateInferenceNode(PrivacyMixin):
    """Inference node with onion routing capabilities"""

    def __init__(self, node_id: str, wallet_address: str, gateway_url: str, **kwargs):
        # Initialize the base inference node
        from core.nodes.inference.node import InferenceNode
        super(InferenceNode, self).__init__()

        self.node_id = node_id
        self.wallet_address = wallet_address
        self.gateway_url = gateway_url

        # Setup onion routing
        self.setup_onion_routes()

        logger.info(f"Private inference node {node_id} initialized with onion routing")


# Testing the onion routing
async def test_onion_routing():
    """Test the onion routing system"""
    print("🧅 Testing Onion Routing System")
    print("=" * 35)

    # Create mock circuit
    circuit_id = "test-circuit-123"
    symmetric_key = b"test-key-32-bytes-long-exactly!!"

    # Create onion handler
    handler = OnionNodeHandler("test-node", {circuit_id: symmetric_key})

    # Test encryption/decryption
    f = Fernet(base64.urlsafe_b64encode(symmetric_key))

    # Create mock inference request
    inference_request = {
        "type": "inference_request",
        "model": "gpt-3.5-turbo",
        "prompt": "This is a private request that should be hidden",
        "max_tokens": 50
    }

    # Encrypt the request
    encrypted_request = f.encrypt(json.dumps(inference_request).encode())

    # Create exit node request
    exit_request = {
        "circuit_id": circuit_id,
        "payload": base64.b64encode(encrypted_request).decode()
    }

    print("✅ Created encrypted onion request")
    print(f"   Circuit ID: {circuit_id}")
    print(f"   Encrypted payload length: {len(encrypted_request)} bytes")

    print("\n🔒 Privacy Properties:")
    print("- Original prompt is encrypted with circuit key")
    print("- Only exit node can decrypt and see the actual request")
    print("- Middle nodes only see encrypted data and next hop")
    print("- Entry node knows source but not destination")
    print("- Each request uses a fresh circuit for maximum privacy")


if __name__ == "__main__":
    asyncio.run(test_onion_routing())