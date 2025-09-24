"""
FastAPI Integration Example

Shows how to build web applications using SolanaLM as the backend LLM service.
"""

import asyncio
import sys
sys.path.append('..')

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

from client.python.solanalm_client import SolanaLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SolanaLM Web App",
    description="Web application powered by SolanaLM decentralized network",
    version="1.0.0"
)

# Configuration
GATEWAY_URL = "http://localhost:8001"
DEFAULT_WALLET = "webapp-wallet-123"


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "gpt-3.5-turbo"
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    wallet_address: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    cost_sol: float
    processing_time: float
    node_id: str


class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 100
    wallet_address: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str
    target_language: str
    wallet_address: Optional[str] = None


# Dependency for SolanaLM client
async def get_solanalm_client():
    """Dependency to get SolanaLM client"""
    return SolanaLMClient(GATEWAY_URL)


# Web API endpoints
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "SolanaLM Web App",
        "version": "1.0.0",
        "description": "Web API powered by decentralized AI network",
        "endpoints": [
            "/chat - Simple chat interface",
            "/summarize - Text summarization",
            "/translate - Language translation",
            "/models - Available models",
            "/health - Service health"
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    client: SolanaLMClient = Depends(get_solanalm_client)
):
    """Simple chat endpoint"""
    try:
        async with client:
            response = await client.inference(
                model=request.model,
                prompt=request.message,
                wallet_address=request.wallet_address or DEFAULT_WALLET,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            return ChatResponse(
                response=response.response,
                model=response.model,
                cost_sol=response.cost_sol,
                processing_time=response.processing_time,
                node_id=response.node_id
            )

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize_endpoint(
    request: SummarizeRequest,
    client: SolanaLMClient = Depends(get_solanalm_client)
):
    """Text summarization endpoint"""
    try:
        # Create summarization prompt
        prompt = f"""Please summarize the following text in {request.max_length} words or less:

Text: {request.text}

Summary:"""

        async with client:
            response = await client.inference(
                model="gpt-3.5-turbo",  # Use a capable model for summarization
                prompt=prompt,
                wallet_address=request.wallet_address or DEFAULT_WALLET,
                max_tokens=request.max_length + 50,  # Some buffer
                temperature=0.3  # Lower temperature for more focused summaries
            )

            return {
                "summary": response.response.strip(),
                "original_length": len(request.text.split()),
                "summary_length": len(response.response.split()),
                "cost_sol": response.cost_sol,
                "model": response.model
            }

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate")
async def translate_endpoint(
    request: TranslateRequest,
    client: SolanaLMClient = Depends(get_solanalm_client)
):
    """Language translation endpoint"""
    try:
        # Create translation prompt
        prompt = f"""Translate the following text to {request.target_language}:

Text: {request.text}

Translation:"""

        async with client:
            response = await client.inference(
                model="gpt-3.5-turbo",
                prompt=prompt,
                wallet_address=request.wallet_address or DEFAULT_WALLET,
                max_tokens=len(request.text.split()) * 2,  # Allow for language expansion
                temperature=0.3  # Lower temperature for accurate translation
            )

            return {
                "translation": response.response.strip(),
                "source_language": "auto-detected",
                "target_language": request.target_language,
                "cost_sol": response.cost_sol,
                "model": response.model
            }

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models_endpoint(client: SolanaLMClient = Depends(get_solanalm_client)):
    """List available models"""
    try:
        async with client:
            models = await client.list_available_models()
            return {"models": models, "count": len(models)}

    except Exception as e:
        logger.error(f"Model listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_endpoint(client: SolanaLMClient = Depends(get_solanalm_client)):
    """Health check endpoint"""
    try:
        async with client:
            status = await client.get_network_status()
            return {
                "status": "healthy",
                "gateway_status": status.get("status", "unknown"),
                "network_stats": status.get("network_stats", {})
            }

    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return {"status": "degraded", "error": str(e)}


# Advanced endpoints for demonstration
@app.post("/batch-process")
async def batch_process_endpoint(
    requests: List[ChatRequest],
    client: SolanaLMClient = Depends(get_solanalm_client)
):
    """Process multiple requests in parallel"""
    if len(requests) > 10:
        raise HTTPException(status_code=400, detail="Too many requests (max 10)")

    try:
        async with client:
            # Process requests concurrently
            tasks = []
            for req in requests:
                task = client.inference(
                    model=req.model,
                    prompt=req.message,
                    wallet_address=req.wallet_address or DEFAULT_WALLET,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Format results
            results = []
            total_cost = 0.0

            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    results.append({
                        "index": i,
                        "error": str(response),
                        "success": False
                    })
                else:
                    results.append({
                        "index": i,
                        "response": response.response,
                        "cost_sol": response.cost_sol,
                        "success": True
                    })
                    total_cost += response.cost_sol

            return {
                "results": results,
                "total_requests": len(requests),
                "successful": sum(1 for r in results if r.get("success", False)),
                "total_cost_sol": total_cost
            }

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cost-estimate")
async def cost_estimate_endpoint(
    text: str,
    model: str = "gpt-3.5-turbo",
    client: SolanaLMClient = Depends(get_solanalm_client)
):
    """Estimate cost for processing text"""
    try:
        # Rough estimation based on token count
        token_count = len(text.split()) * 1.3  # Rough tokens-to-words ratio

        # Mock cost calculation (in practice, query network for pricing)
        estimated_cost_sol = token_count * 0.0001  # Example rate

        return {
            "text_length": len(text),
            "estimated_tokens": int(token_count),
            "estimated_cost_sol": estimated_cost_sol,
            "model": model,
            "note": "Estimate only - actual cost may vary"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# HTML frontend for testing (simple demo)
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>SolanaLM Web App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        textarea { width: 100%; height: 100px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; }
        .response { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 SolanaLM Web App</h1>
        <p>Powered by decentralized AI network</p>

        <h2>Chat Interface</h2>
        <textarea id="chatInput" placeholder="Enter your message..."></textarea><br>
        <button onclick="sendChat()">Send Message</button>
        <div id="chatResponse" class="response" style="display:none;"></div>

        <h2>Text Summarization</h2>
        <textarea id="summaryInput" placeholder="Enter text to summarize..."></textarea><br>
        <button onclick="summarizeText()">Summarize</button>
        <div id="summaryResponse" class="response" style="display:none;"></div>

        <script>
            async function sendChat() {
                const input = document.getElementById('chatInput').value;
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: input })
                });
                const data = await response.json();
                document.getElementById('chatResponse').innerHTML =
                    `<strong>Response:</strong> ${data.response}<br>
                     <small>Cost: ${data.cost_sol} SOL | Model: ${data.model}</small>`;
                document.getElementById('chatResponse').style.display = 'block';
            }

            async function summarizeText() {
                const input = document.getElementById('summaryInput').value;
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: input, max_length: 50 })
                });
                const data = await response.json();
                document.getElementById('summaryResponse').innerHTML =
                    `<strong>Summary:</strong> ${data.summary}<br>
                     <small>Reduced from ${data.original_length} to ${data.summary_length} words</small>`;
                document.getElementById('summaryResponse').style.display = 'block';
            }
        </script>
    </div>
</body>
</html>
"""

@app.get("/demo", response_class=lambda content, *args, **kwargs: content, content_type="text/html")
async def demo_frontend():
    """Simple HTML frontend for testing"""
    return html_content


if __name__ == "__main__":
    import uvicorn

    print("🌐 Starting SolanaLM Web App")
    print("=" * 40)
    print("API Documentation: http://localhost:8000/docs")
    print("Demo Interface: http://localhost:8000/demo")
    print("Health Check: http://localhost:8000/health")
    print("\n⚠️  Make sure SolanaLM gateway is running on port 8001")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)