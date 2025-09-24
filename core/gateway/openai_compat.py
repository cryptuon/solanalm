"""
OpenAI-Compatible API Endpoints

Drop-in replacement for OpenAI API that routes to SolanaLM network.
Developers can use existing OpenAI client libraries with SolanaLM.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
import time
import uuid
from datetime import datetime

from core.models.schemas import InferenceRequest, InferenceResponse
from core.registry.node_registry import NodeRegistry
from core.payments.solana_client import SolanaPaymentClient

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])

# Global registry access (injected from main app)
node_registry: Optional[NodeRegistry] = None
payment_client: Optional[SolanaPaymentClient] = None


# OpenAI-Compatible Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use")
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    max_tokens: Optional[int] = Field(default=100, description="Max tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = Field(default=False, description="Stream response")
    user: Optional[str] = Field(default=None, description="User identifier")


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[Model]


# Legacy Completions API
class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = Field(default=100)
    temperature: Optional[float] = Field(default=0.7)
    top_p: Optional[float] = Field(default=1.0)
    stream: Optional[bool] = Field(default=False)


class CompletionChoice(BaseModel):
    text: str
    index: int
    finish_reason: str


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: ChatCompletionUsage


def extract_wallet_from_auth(authorization: str) -> str:
    """Extract Solana wallet from Authorization header"""
    # Format: "Bearer wallet_address" or "Bearer sk-wallet_address"
    if not authorization:
        return "anonymous_wallet"

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return "anonymous_wallet"

    token = parts[1]
    # If it starts with sk-, extract wallet after the sk- prefix
    if token.startswith("sk-"):
        return token[3:]  # Remove "sk-" prefix

    return token


def convert_messages_to_prompt(messages: List[ChatMessage]) -> str:
    """Convert chat messages to a single prompt"""
    prompt_parts = []

    for message in messages:
        role = message.role
        content = message.content

        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")

    # Add assistant prompt to continue conversation
    prompt_parts.append("Assistant:")

    return "\n".join(prompt_parts)


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """List available models (OpenAI compatible)"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Service not available")

    try:
        nodes = await node_registry.get_all_nodes()

        # Collect unique models
        models = set()
        for node in nodes:
            models.update(node.supported_models)

        model_list = []
        for i, model_name in enumerate(sorted(models)):
            model_list.append(Model(
                id=model_name,
                created=int(time.time()),
                owned_by="solanalm"
            ))

        return ModelListResponse(data=model_list)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """Create chat completion (OpenAI compatible)"""
    if not node_registry or not payment_client:
        raise HTTPException(status_code=503, detail="Service not available")

    # Extract wallet from authorization header
    wallet_address = extract_wallet_from_auth(authorization)

    # Convert chat messages to prompt
    prompt = convert_messages_to_prompt(request.messages)

    # Create internal inference request
    inference_request = InferenceRequest(
        model=request.model,
        prompt=prompt,
        wallet_address=wallet_address,
        max_tokens=request.max_tokens or 100,
        temperature=request.temperature or 0.7,
        top_p=request.top_p or 1.0,
        metadata={"openai_compat": True, "user": request.user}
    )

    try:
        # Find best node
        node = await node_registry.find_best_node(
            model=request.model,
            node_type="inference"
        )

        if not node:
            raise HTTPException(
                status_code=503,
                detail="No available nodes for requested model"
            )

        # Process inference
        response = await node.process_inference(inference_request)

        # Convert to OpenAI format
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        chat_response = ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response.response.strip()
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(prompt.split()),  # Rough estimate
                completion_tokens=response.tokens_generated,
                total_tokens=len(prompt.split()) + response.tokens_generated
            )
        )

        return chat_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """Create text completion (OpenAI compatible - legacy)"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Service not available")

    wallet_address = extract_wallet_from_auth(authorization)

    # Create internal inference request
    inference_request = InferenceRequest(
        model=request.model,
        prompt=request.prompt,
        wallet_address=wallet_address,
        max_tokens=request.max_tokens or 100,
        temperature=request.temperature or 0.7,
        top_p=request.top_p or 1.0,
        metadata={"openai_compat": True, "legacy_completion": True}
    )

    try:
        # Find best node
        node = await node_registry.find_best_node(
            model=request.model,
            node_type="inference"
        )

        if not node:
            raise HTTPException(
                status_code=503,
                detail="No available nodes for requested model"
            )

        # Process inference
        response = await node.process_inference(inference_request)

        # Convert to OpenAI format
        completion_id = f"cmpl-{uuid.uuid4().hex[:12]}"

        completion_response = CompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    text=response.response,
                    index=0,
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(request.prompt.split()),
                completion_tokens=response.tokens_generated,
                total_tokens=len(request.prompt.split()) + response.tokens_generated
            )
        )

        return completion_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def openai_health():
    """Health check for OpenAI-compatible API"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "compatibility": "openai",
        "timestamp": datetime.utcnow().isoformat()
    }


def init_openai_compat_router(registry: NodeRegistry, payment: SolanaPaymentClient):
    """Initialize the OpenAI compatibility router with dependencies"""
    global node_registry, payment_client
    node_registry = registry
    payment_client = payment