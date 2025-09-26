"""
Enhanced Inference Node with Multiple Backend Support
Supports: Transformers, llama.cpp, OpenAI API, Ollama, Local APIs
"""

import asyncio
import logging
import time
import json
import aiohttp
from typing import Optional, Dict, Any, Union
from enum import Enum

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from fastapi import FastAPI, HTTPException
import uvicorn

from core.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    NodeCapabilities,
    NodeType,
    NodeStatus,
    HardwareSpecs,
    PricingConfig
)

logger = logging.getLogger(__name__)


class ModelBackend(str, Enum):
    """Supported model backends"""
    TRANSFORMERS = "transformers"
    LLAMA_CPP = "llama_cpp"
    OPENAI_API = "openai"
    ANTHROPIC_API = "anthropic"
    OLLAMA = "ollama"
    CUSTOM_API = "custom_api"


class EnhancedInferenceNode:
    """Enhanced inference node supporting multiple backends"""

    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        backend: ModelBackend = ModelBackend.TRANSFORMERS,
        model_name: str = "microsoft/DialoGPT-small",
        model_path: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8100
    ):
        self.node_id = node_id
        self.wallet_address = wallet_address
        self.gateway_url = gateway_url
        self.backend = ModelBackend(backend)
        self.model_name = model_name
        self.model_path = model_path
        self.api_key = api_key
        self.api_url = api_url
        self.host = host
        self.port = port

        # Backend-specific components
        self.tokenizer = None
        self.model = None
        self.llama_model = None
        self.client = None

        # State management
        self.is_ready = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu" if HAS_TRANSFORMERS else "cpu"

        # Statistics
        self.requests_served = 0
        self.total_tokens_generated = 0
        self.total_processing_time = 0.0
        self.errors = 0

        # FastAPI app
        self.app = FastAPI(title=f"Enhanced Inference Node {node_id}")
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy" if self.is_ready else "initializing",
                "backend": self.backend.value,
                "model": self.model_name,
                "device": self.device,
                "stats": {
                    "requests_served": self.requests_served,
                    "total_tokens_generated": self.total_tokens_generated,
                    "total_processing_time": self.total_processing_time,
                    "errors": self.errors
                }
            }

        @self.app.post("/inference")
        async def inference_endpoint(request: InferenceRequest):
            return await self.process_inference(request)

    async def initialize(self):
        """Initialize the appropriate backend"""
        logger.info(f"Initializing enhanced inference node {self.node_id} with {self.backend.value} backend")

        try:
            if self.backend == ModelBackend.TRANSFORMERS:
                await self._init_transformers()
            elif self.backend == ModelBackend.LLAMA_CPP:
                await self._init_llama_cpp()
            elif self.backend == ModelBackend.OPENAI_API:
                await self._init_openai()
            elif self.backend == ModelBackend.OLLAMA:
                await self._init_ollama()
            elif self.backend == ModelBackend.CUSTOM_API:
                await self._init_custom_api()
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")

            self.is_ready = True
            logger.info(f"Backend {self.backend.value} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize backend {self.backend.value}: {e}")
            raise

    async def _init_transformers(self):
        """Initialize Transformers backend"""
        if not HAS_TRANSFORMERS:
            raise ImportError("Transformers not available")

        logger.info(f"Loading Transformers model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = self.model.to(self.device)
        self.model.eval()

    async def _init_llama_cpp(self):
        """Initialize llama.cpp backend"""
        if not HAS_LLAMA_CPP:
            raise ImportError("llama-cpp-python not available")

        if not self.model_path:
            raise ValueError("model_path required for llama.cpp backend")

        logger.info(f"Loading llama.cpp model: {self.model_path}")
        self.llama_model = Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )

    async def _init_openai(self):
        """Initialize OpenAI API backend"""
        if not HAS_OPENAI:
            raise ImportError("openai not available")

        if not self.api_key:
            raise ValueError("API key required for OpenAI backend")

        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def _init_ollama(self):
        """Initialize Ollama backend"""
        self.api_url = self.api_url or "http://localhost:11434"
        logger.info(f"Connecting to Ollama at {self.api_url}")

    async def _init_custom_api(self):
        """Initialize custom API backend"""
        if not self.api_url:
            raise ValueError("API URL required for custom API backend")

        logger.info(f"Connecting to custom API at {self.api_url}")

    async def process_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Process inference request using appropriate backend"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Node not ready")

        start_time = time.time()

        try:
            if self.backend == ModelBackend.TRANSFORMERS:
                response_text = await self._process_transformers(request)
            elif self.backend == ModelBackend.LLAMA_CPP:
                response_text = await self._process_llama_cpp(request)
            elif self.backend == ModelBackend.OPENAI_API:
                response_text = await self._process_openai(request)
            elif self.backend == ModelBackend.OLLAMA:
                response_text = await self._process_ollama(request)
            elif self.backend == ModelBackend.CUSTOM_API:
                response_text = await self._process_custom_api(request)
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")

            processing_time = time.time() - start_time
            tokens_generated = len(response_text.split())

            # Update statistics
            self.requests_served += 1
            self.total_tokens_generated += tokens_generated
            self.total_processing_time += processing_time

            return InferenceResponse(
                response=response_text,
                model=self.model_name,
                tokens_generated=tokens_generated,
                processing_time=processing_time,
                node_id=self.node_id
            )

        except Exception as e:
            self.errors += 1
            logger.error(f"Inference failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _process_transformers(self, request: InferenceRequest) -> str:
        """Process using Transformers"""
        inputs = self.tokenizer.encode(request.prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.size(1) + request.max_tokens,
                do_sample=True,
                temperature=request.temperature,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(request.prompt):].strip()

    async def _process_llama_cpp(self, request: InferenceRequest) -> str:
        """Process using llama.cpp"""
        output = self.llama_model(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            echo=False
        )
        return output['choices'][0]['text']

    async def _process_openai(self, request: InferenceRequest) -> str:
        """Process using OpenAI API"""
        response = await self.client.chat.completions.create(
            model=self.model_name or "gpt-3.5-turbo",
            messages=[{"role": "user", "content": request.prompt}],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return response.choices[0].message.content

    async def _process_ollama(self, request: InferenceRequest) -> str:
        """Process using Ollama"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model_name,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens
                }
            }

            async with session.post(f"{self.api_url}/api/generate", json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama API error: {resp.status}")

                result = await resp.json()
                return result.get("response", "")

    async def _process_custom_api(self, request: InferenceRequest) -> str:
        """Process using custom API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with session.post(self.api_url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Custom API error: {resp.status}")

                result = await resp.json()
                return result.get("response", result.get("text", ""))

    async def run(self):
        """Start the inference node server"""
        logger.info(f"Starting enhanced inference node on {self.host}:{self.port}")
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Convenience functions for different backends
async def create_transformers_node(node_id: str, wallet: str, gateway: str, model: str, port: int = 8100):
    """Create a Transformers-based inference node"""
    node = EnhancedInferenceNode(
        node_id=node_id,
        wallet_address=wallet,
        gateway_url=gateway,
        backend=ModelBackend.TRANSFORMERS,
        model_name=model,
        port=port
    )
    await node.initialize()
    return node


async def create_llama_cpp_node(node_id: str, wallet: str, gateway: str, model_path: str, port: int = 8101):
    """Create a llama.cpp-based inference node"""
    node = EnhancedInferenceNode(
        node_id=node_id,
        wallet_address=wallet,
        gateway_url=gateway,
        backend=ModelBackend.LLAMA_CPP,
        model_name="llama-cpp",
        model_path=model_path,
        port=port
    )
    await node.initialize()
    return node


async def create_openai_proxy_node(node_id: str, wallet: str, gateway: str, api_key: str, model: str = "gpt-3.5-turbo", port: int = 8102):
    """Create an OpenAI proxy node"""
    node = EnhancedInferenceNode(
        node_id=node_id,
        wallet_address=wallet,
        gateway_url=gateway,
        backend=ModelBackend.OPENAI_API,
        model_name=model,
        api_key=api_key,
        port=port
    )
    await node.initialize()
    return node


async def create_ollama_proxy_node(node_id: str, wallet: str, gateway: str, model: str, ollama_url: str = "http://localhost:11434", port: int = 8103):
    """Create an Ollama proxy node"""
    node = EnhancedInferenceNode(
        node_id=node_id,
        wallet_address=wallet,
        gateway_url=gateway,
        backend=ModelBackend.OLLAMA,
        model_name=model,
        api_url=ollama_url,
        port=port
    )
    await node.initialize()
    return node