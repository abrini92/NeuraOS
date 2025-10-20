"""
Cortex types and data models.

Defines Pydantic models for Cortex requests, responses, and configuration.
"""

from enum import Enum

from pydantic import BaseModel, Field


class OllamaModel(str, Enum):
    """Supported Ollama models."""

    MISTRAL = "mistral"
    LLAMA3 = "llama3"
    GEMMA = "gemma"
    LLAMA2 = "llama2"
    CODELLAMA = "codellama"


class GenerateRequest(BaseModel):
    """
    Request model for text generation.

    Example:
        >>> request = GenerateRequest(
        ...     prompt="What is Neura?",
        ...     model="mistral",
        ...     temperature=0.7
        ... )
    """

    prompt: str = Field(..., description="The prompt to generate from", min_length=1)
    model: str = Field(default="mistral", description="Model to use for generation")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)"
    )
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens to generate")
    stream: bool = Field(default=False, description="Enable streaming response")
    context: list[str] | None = Field(default=None, description="Optional context from memory")
    system_prompt: str | None = Field(default=None, description="Optional system prompt override")


class GenerateResponse(BaseModel):
    """
    Response model for text generation.

    Example:
        >>> response = GenerateResponse(
        ...     text="Neura is a local-first cognitive OS",
        ...     model="mistral",
        ...     tokens_generated=10
        ... )
    """

    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")
    tokens_generated: int = Field(..., description="Number of tokens generated")
    finished: bool = Field(default=True, description="Whether generation finished")
    context_used: bool = Field(default=False, description="Whether context from memory was used")


class OllamaModelInfo(BaseModel):
    """Information about an Ollama model."""

    name: str = Field(..., description="Model name")
    size: int | str | None = Field(
        None, description="Model size in bytes (int) or human-readable (str)"
    )
    modified_at: str | None = Field(None, description="Last modified timestamp")


class OllamaStatus(BaseModel):
    """Status of Ollama service."""

    available: bool = Field(..., description="Whether Ollama is available")
    version: str | None = Field(None, description="Ollama version")
    models: list[str] = Field(default_factory=list, description="Available models")
    error: str | None = Field(None, description="Error message if unavailable")


class CortexConfig(BaseModel):
    """Configuration for Cortex module."""

    ollama_host: str = Field(default="http://localhost:11434", description="Ollama host URL")
    default_model: str = Field(default="mistral", description="Default model to use")
    default_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature"
    )
    default_max_tokens: int = Field(default=2048, ge=1, description="Default max tokens")
    timeout: int = Field(default=120, ge=1, description="Request timeout in seconds")
    system_prompt: str = Field(
        default=(
            "You are Neura, a local-first cognitive operating system. "
            "You are helpful, ethical, and always respect user privacy. "
            "All your processing happens locally, with no data sent to external servers."
        ),
        description="Default system prompt",
    )
