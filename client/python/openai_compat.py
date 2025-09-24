"""
OpenAI-Compatible Client

Drop-in replacement for OpenAI's Python client that routes to SolanaLM network.
Allows developers to use existing code with minimal changes.
"""

import asyncio
import aiohttp
import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
import json
import time

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatCompletion:
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@dataclass
class Completion:
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@dataclass
class Model:
    id: str
    object: str
    created: int
    owned_by: str


class SolanaLMOpenAI:
    """
    Drop-in replacement for OpenAI client that uses SolanaLM network.

    Usage:
        # Instead of: import openai
        from solanalm import SolanaLMOpenAI as openai

        # Set your Solana wallet as API key
        openai.api_key = "your-solana-wallet-address"
        openai.api_base = "http://localhost:8001/v1"  # SolanaLM gateway

        # Use exactly like OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """

    api_key: str = "anonymous_wallet"
    api_base: str = "http://localhost:8001/v1"
    timeout: int = 60

    class ChatCompletion:
        @classmethod
        def create(
            cls,
            model: str,
            messages: List[Dict[str, str]],
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            stream: Optional[bool] = False,
            **kwargs
        ) -> ChatCompletion:
            """Create chat completion (synchronous)"""
            return asyncio.run(cls.acreate(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream,
                **kwargs
            ))

        @classmethod
        async def acreate(
            cls,
            model: str,
            messages: List[Dict[str, str]],
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            stream: Optional[bool] = False,
            **kwargs
        ) -> ChatCompletion:
            """Create chat completion (asynchronous)"""

            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens or 100,
                "temperature": temperature or 0.7,
                "top_p": top_p or 1.0,
                "stream": stream
            }

            headers = {
                "Authorization": f"Bearer {SolanaLMOpenAI.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SolanaLMOpenAI.api_base}/chat/completions",
                    json=request_data,
                    headers=headers,
                    timeout=SolanaLMOpenAI.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"SolanaLM API error: {response.status} - {error_text}")

                    data = await response.json()

                    return ChatCompletion(
                        id=data["id"],
                        object=data["object"],
                        created=data["created"],
                        model=data["model"],
                        choices=data["choices"],
                        usage=data["usage"]
                    )

    class Completion:
        @classmethod
        def create(
            cls,
            model: str,
            prompt: str,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            **kwargs
        ) -> Completion:
            """Create text completion (synchronous, legacy API)"""
            return asyncio.run(cls.acreate(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs
            ))

        @classmethod
        async def acreate(
            cls,
            model: str,
            prompt: str,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            **kwargs
        ) -> Completion:
            """Create text completion (asynchronous)"""

            request_data = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens or 100,
                "temperature": temperature or 0.7,
                "top_p": top_p or 1.0
            }

            headers = {
                "Authorization": f"Bearer {SolanaLMOpenAI.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SolanaLMOpenAI.api_base}/completions",
                    json=request_data,
                    headers=headers,
                    timeout=SolanaLMOpenAI.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"SolanaLM API error: {response.status} - {error_text}")

                    data = await response.json()

                    return Completion(
                        id=data["id"],
                        object=data["object"],
                        created=data["created"],
                        model=data["model"],
                        choices=data["choices"],
                        usage=data["usage"]
                    )

    class Model:
        @classmethod
        def list(cls) -> Dict[str, List[Model]]:
            """List available models (synchronous)"""
            return asyncio.run(cls.alist())

        @classmethod
        async def alist(cls) -> Dict[str, List[Model]]:
            """List available models (asynchronous)"""
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SolanaLMOpenAI.api_base}/models",
                    timeout=SolanaLMOpenAI.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"SolanaLM API error: {response.status} - {error_text}")

                    data = await response.json()

                    models = []
                    for model_data in data["data"]:
                        models.append(Model(
                            id=model_data["id"],
                            object=model_data["object"],
                            created=model_data["created"],
                            owned_by=model_data["owned_by"]
                        ))

                    return {"object": "list", "data": models}


# Create global instance that can be imported like OpenAI
openai = SolanaLMOpenAI()

# Export the same interface as OpenAI
ChatCompletion = SolanaLMOpenAI.ChatCompletion
Completion = SolanaLMOpenAI.Completion
Model = SolanaLMOpenAI.Model


def set_api_key(key: str):
    """Set API key (Solana wallet address)"""
    SolanaLMOpenAI.api_key = key
    openai.api_key = key


def set_api_base(base: str):
    """Set API base URL"""
    SolanaLMOpenAI.api_base = base
    openai.api_base = base


# Convenience functions for common patterns
async def chat(
    message: str,
    model: str = "gpt-3.5-turbo",
    wallet: Optional[str] = None,
    **kwargs
) -> str:
    """Simple chat function"""
    if wallet:
        old_key = SolanaLMOpenAI.api_key
        SolanaLMOpenAI.api_key = wallet

    try:
        response = await ChatCompletion.acreate(
            model=model,
            messages=[{"role": "user", "content": message}],
            **kwargs
        )
        return response.choices[0]["message"]["content"]
    finally:
        if wallet:
            SolanaLMOpenAI.api_key = old_key


def chat_sync(
    message: str,
    model: str = "gpt-3.5-turbo",
    wallet: Optional[str] = None,
    **kwargs
) -> str:
    """Simple synchronous chat function"""
    return asyncio.run(chat(message, model, wallet, **kwargs))


# Example usage and migration guide
if __name__ == "__main__":
    print("SolanaLM OpenAI-Compatible Client")
    print("=" * 40)

    # Example: Migrating from OpenAI to SolanaLM
    print("\n🔄 Migration Example:")
    print("# BEFORE (OpenAI):")
    print("import openai")
    print("openai.api_key = 'sk-your-openai-key'")
    print("response = openai.ChatCompletion.create(...)")

    print("\n# AFTER (SolanaLM):")
    print("from solanalm.client.python.openai_compat import openai")
    print("openai.api_key = 'your-solana-wallet-address'")
    print("openai.api_base = 'http://localhost:8001/v1'")
    print("response = openai.ChatCompletion.create(...)  # Same API!")

    print("\n✨ Benefits:")
    print("- Same familiar API")
    print("- No code changes needed")
    print("- Decentralized network")
    print("- Lower costs with SOL payments")
    print("- Support for local and proxy models")

    # Test basic functionality
    async def test_functionality():
        print("\n🧪 Testing functionality...")

        # Set test configuration
        set_api_key("test-wallet-123")
        set_api_base("http://localhost:8001/v1")

        try:
            # Test model listing
            models = await Model.alist()
            print(f"Available models: {len(models.get('data', []))}")

            # Test simple chat (would need running gateway)
            # response = await chat("Hello, world!")
            # print(f"Response: {response}")

        except Exception as e:
            print(f"Test failed (expected if gateway not running): {e}")

    # Run test
    asyncio.run(test_functionality())