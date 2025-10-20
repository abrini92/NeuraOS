"""
Cortex API router - FastAPI endpoints for LLM operations.

Provides REST endpoints for text generation, model management, and status checks.
"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from neura.core.config import get_settings
from neura.cortex.engine import get_ollama_client
from neura.cortex.types import (
    CortexConfig,
    GenerateRequest,
    GenerateResponse,
    OllamaModelInfo,
    OllamaStatus,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text using local LLM.

    Args:
        request: Generation request with prompt and parameters

    Returns:
        GenerateResponse: Generated text

    Raises:
        HTTPException: If generation fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/cortex/generate \
          -H "Content-Type: application/json" \
          -d '{"prompt": "Hello, who are you?", "model": "mistral"}'
        ```
    """
    logger.info(f"Generate request: prompt_length={len(request.prompt)}, stream={request.stream}")

    # Get Ollama client
    settings = get_settings()
    config = CortexConfig(
        ollama_host="http://localhost:11434",
        default_model=settings.cortex_model,
        default_temperature=settings.cortex_temperature,
        default_max_tokens=settings.cortex_max_tokens,
    )
    client = get_ollama_client(config)

    # Handle streaming
    if request.stream:

        async def generate_stream() -> dict:
            """Stream generator for SSE."""
            try:
                async for chunk in client.generate_stream(request):
                    if chunk.is_success():
                        yield f"data: {chunk.data}\n\n"
                    else:
                        yield f"data: [ERROR] {chunk.error}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: [ERROR] {str(e)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
        )

    # Non-streaming generation
    result = await client.generate(request)

    if result.is_failure():
        logger.error(f"Generation failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@router.post("/stream")
async def stream_generate(request: GenerateRequest):
    """
    Stream LLM response in real-time (SSE).
    
    Args:
        request: Generation request
        
    Returns:
        StreamingResponse: Server-Sent Events stream
        
    Example:
        ```bash
        curl -X POST http://localhost:8000/api/cortex/stream \
          -H "Content-Type: application/json" \
          -d '{"prompt": "Tell me a story"}' \
          --no-buffer
        ```
    """
    logger.info(f"Stream request: prompt_length={len(request.prompt)}")
    
    # Force streaming
    request.stream = True
    
    # Get client
    settings = get_settings()
    config = CortexConfig(
        ollama_host="http://localhost:11434",
        default_model=settings.cortex_model,
    )
    client = get_ollama_client(config)
    
    async def generate():
        """SSE generator."""
        try:
            async for chunk in client.generate_stream(request):
                if chunk.is_success():
                    yield f"data: {chunk.data}\n\n"
                else:
                    yield f"data: [ERROR] {chunk.error}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/models", response_model=list[OllamaModelInfo])
async def list_models() -> list[OllamaModelInfo]:
    """
    List available Ollama models.

    Returns:
        List[OllamaModelInfo]: Available models

    Raises:
        HTTPException: If model listing fails

    Example:
        ```bash
        curl http://localhost:8000/api/cortex/models
        ```
    """
    logger.debug("Listing available models")

    config = CortexConfig()
    client = get_ollama_client(config)

    result = await client.list_models()

    if result.is_failure():
        logger.error(f"Failed to list models: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@router.get("/status", response_model=OllamaStatus)
async def get_status() -> OllamaStatus:
    """
    Check Ollama service status.

    Returns:
        OllamaStatus: Service status and available models

    Example:
        ```bash
        curl http://localhost:8000/api/cortex/status
        ```
    """
    logger.debug("Checking Ollama status")

    config = CortexConfig()
    client = get_ollama_client(config)

    status = await client.check_status()
    return status


@router.get("/")
async def cortex_info() -> dict:
    """
    Get Cortex module information.

    Returns:
        dict: Module information
    """
    return {
        "module": "cortex",
        "status": "operational",
        "description": "Local LLM reasoning engine",
        "endpoints": {
            "generate": "/api/cortex/generate",
            "models": "/api/cortex/models",
            "status": "/api/cortex/status",
        },
    }
