"""
Cortex engine - Local LLM inference via Ollama.

This module provides the OllamaClient for interacting with local LLM models
through the Ollama API.
"""

import logging
from collections.abc import AsyncIterator

import httpx

from neura.core.events import get_event_bus
from neura.core.types import Result
from neura.cortex.types import (
    CortexConfig,
    GenerateRequest,
    GenerateResponse,
    OllamaModelInfo,
    OllamaStatus,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama API.

    This client handles all communication with the local Ollama instance,
    including text generation, model listing, and health checks.

    Example:
        >>> client = OllamaClient(config)
        >>> result = await client.generate(request)
        >>> if result.is_success():
        ...     print(result.data.text)
    """

    def __init__(self, config: CortexConfig) -> None:
        """
        Initialize Ollama client.

        Args:
            config: Cortex configuration
        """
        self.config = config
        self._client = httpx.AsyncClient(timeout=config.timeout)
        logger.info(f"OllamaClient initialized (host: {config.ollama_host})")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.debug("OllamaClient closed")

    async def generate(self, request: GenerateRequest) -> Result[GenerateResponse]:
        """
        Generate text using Ollama.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            Result[GenerateResponse]: Generated text or error

        Example:
            >>> req = GenerateRequest(prompt="Hello, who are you?")
            >>> result = await client.generate(req)
            >>> if result.is_success():
            ...     print(result.data.text)
        """
        try:
            # Build system prompt
            system_prompt = request.system_prompt or self.config.system_prompt

            # Add context if provided
            full_prompt = request.prompt
            if request.context:
                context_str = "\n\n".join(request.context)
                full_prompt = f"Context:\n{context_str}\n\nUser: {request.prompt}"
                logger.debug(f"Added context to prompt ({len(request.context)} items)")

            # Prepare Ollama request
            ollama_request = {
                "model": request.model or self.config.default_model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }

            logger.info(
                f"Generating with model={ollama_request['model']}, " f"temp={request.temperature}"
            )

            # Call Ollama API
            response = await self._client.post(
                f"{self.config.ollama_host}/api/generate",
                json=ollama_request,
            )

            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return Result.failure(error_msg)

            data = response.json()

            # Build response
            generated_text = data.get("response", "")
            tokens_generated = len(generated_text.split())  # Approximate token count

            result = GenerateResponse(
                text=generated_text,
                model=ollama_request["model"],
                tokens_generated=tokens_generated,
                finished=data.get("done", True),
                context_used=bool(request.context),
            )

            logger.info(f"Generated {tokens_generated} tokens")

            # Publish event to event bus
            event_bus = get_event_bus()
            await event_bus.publish(
                "cortex.generated",
                {
                    "model": result.model,
                    "tokens": tokens_generated,
                    "context_used": result.context_used,
                },
                source="cortex",
            )

            return Result.success(result)

        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to Ollama at {self.config.ollama_host}: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

        except httpx.TimeoutException as e:
            error_msg = f"Ollama request timed out: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error during generation: {e}"
            logger.error(error_msg, exc_info=True)
            return Result.failure(error_msg)

    async def generate_stream(self, request: GenerateRequest) -> AsyncIterator[Result[str]]:
        """
        Generate text with streaming.

        Yields chunks of text as they are generated.

        Args:
            request: Generation request

        Yields:
            Result[str]: Text chunks or errors

        Example:
            >>> req = GenerateRequest(prompt="Tell me a story", stream=True)
            >>> async for chunk in client.generate_stream(req):
            ...     if chunk.is_success():
            ...         print(chunk.data, end="")
        """
        try:
            # Build system prompt
            system_prompt = request.system_prompt or self.config.system_prompt

            # Add context if provided
            full_prompt = request.prompt
            if request.context:
                context_str = "\n\n".join(request.context)
                full_prompt = f"Context:\n{context_str}\n\nUser: {request.prompt}"

            # Prepare Ollama request
            ollama_request = {
                "model": request.model or self.config.default_model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": True,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }

            logger.info(f"Streaming generation with model={ollama_request['model']}")

            # Stream from Ollama
            async with self._client.stream(
                "POST",
                f"{self.config.ollama_host}/api/generate",
                json=ollama_request,
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Ollama API error: {response.status_code}"
                    logger.error(error_msg)
                    yield Result.failure(error_msg)
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        import json

                        data = json.loads(line)
                        chunk = data.get("response", "")
                        if chunk:
                            yield Result.success(chunk)

                        if data.get("done", False):
                            # Publish completion event
                            event_bus = get_event_bus()
                            await event_bus.publish(
                                "cortex.generated",
                                {
                                    "model": ollama_request["model"],
                                    "stream": True,
                                    "context_used": bool(request.context),
                                },
                                source="cortex",
                            )
                            break

                    except Exception as e:
                        logger.error(f"Error parsing stream chunk: {e}")
                        continue

        except Exception as e:
            error_msg = f"Streaming error: {e}"
            logger.error(error_msg, exc_info=True)
            yield Result.failure(error_msg)

    async def list_models(self) -> Result[list[OllamaModelInfo]]:
        """
        List available Ollama models.

        Returns:
            Result[List[OllamaModelInfo]]: List of available models or error
        """
        try:
            logger.debug("Listing Ollama models")
            response = await self._client.get(f"{self.config.ollama_host}/api/tags")

            if response.status_code != 200:
                error_msg = f"Failed to list models: {response.status_code}"
                logger.error(error_msg)
                return Result.failure(error_msg)

            data = response.json()
            models = [
                OllamaModelInfo(
                    name=model.get("name", "unknown"),
                    size=model.get("size"),
                    modified_at=model.get("modified_at"),
                )
                for model in data.get("models", [])
            ]

            logger.info(f"Found {len(models)} Ollama models")
            return Result.success(models)

        except Exception as e:
            error_msg = f"Error listing models: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def check_status(self) -> OllamaStatus:
        """
        Check if Ollama is available and get status.

        Returns:
            OllamaStatus: Status information
        """
        try:
            # Try to get version
            response = await self._client.get(f"{self.config.ollama_host}/api/version", timeout=5.0)

            if response.status_code == 200:
                version = response.json().get("version", "unknown")
            else:
                version = None

            # Get models
            models_result = await self.list_models()
            models = [m.name for m in models_result.data] if models_result.is_success() else []

            return OllamaStatus(
                available=True,
                version=version,
                models=models,
            )

        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return OllamaStatus(
                available=False,
                error=str(e),
            )


# Singleton instance
_ollama_client: OllamaClient | None = None


def get_ollama_client(config: CortexConfig | None = None) -> OllamaClient:
    """
    Get the global Ollama client instance.

    Args:
        config: Optional configuration (used for first initialization)

    Returns:
        OllamaClient: The singleton client
    """
    global _ollama_client
    if _ollama_client is None:
        if config is None:
            # Use default config
            config = CortexConfig()
        _ollama_client = OllamaClient(config)
    return _ollama_client


async def close_ollama_client() -> None:
    """Close the global Ollama client."""
    global _ollama_client
    if _ollama_client is not None:
        await _ollama_client.close()
        _ollama_client = None
