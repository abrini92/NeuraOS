"""
Cortex module - Local LLM reasoning and contextual generation.

The Cortex is Neura's thinking engine, providing:
- Local LLM inference via Ollama
- Contextual reasoning with memory integration
- Prompt engineering and response generation
"""

from neura.cortex.engine import OllamaClient, get_ollama_client
from neura.cortex.router import router
from neura.cortex.types import (
    CortexConfig,
    GenerateRequest,
    GenerateResponse,
    OllamaModelInfo,
    OllamaStatus,
)

__all__ = [
    "OllamaClient",
    "get_ollama_client",
    "router",
    "CortexConfig",
    "GenerateRequest",
    "GenerateResponse",
    "OllamaModelInfo",
    "OllamaStatus",
]
