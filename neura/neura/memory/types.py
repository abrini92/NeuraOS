"""
Memory types and data models.

Defines Pydantic models for memory entries, context windows, and recall results.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Type of memory entry."""

    NOTE = "note"
    CONVERSATION = "conversation"
    OBSERVATION = "observation"
    THOUGHT = "thought"
    DECISION = "decision"
    LEARNING = "learning"


class ChunkMetadata(BaseModel):
    """Metadata for a content chunk."""

    parent_id: str = Field(..., description="ID of the parent document")
    chunk_index: int = Field(..., description="Index of this chunk in the document")
    total_chunks: int = Field(..., description="Total number of chunks")
    overlap_start: int = Field(default=0, description="Overlap start position")
    overlap_end: int = Field(default=0, description="Overlap end position")


class MemoryEntry(BaseModel):
    """
    A memory entry stored in the graph.

    Example:
        >>> entry = MemoryEntry(
        ...     id="mem_123",
        ...     content="Neura is a local-first cognitive OS",
        ...     content_hash="abc123...",
        ...     metadata={"type": "note"}
        ... )
    """

    id: str = Field(..., description="Unique memory ID")
    content: str = Field(..., description="Memory content")
    content_hash: str = Field(..., description="SHA256 hash of content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    memory_type: MemoryType = Field(default=MemoryType.NOTE, description="Type of memory")
    embedding_model: str | None = Field(None, description="Model used for embeddings")
    chunk_metadata: ChunkMetadata | None = Field(None, description="Chunk information")


class RecallResult(BaseModel):
    """Result from a memory recall operation."""

    entry: MemoryEntry = Field(..., description="The recalled memory entry")
    score: float = Field(..., description="Relevance score (0-1)")
    source: str = Field(..., description="Source of result (fts, semantic, hybrid)")


class ContextWindow(BaseModel):
    """
    Conversational context window.

    Manages a sliding window of conversation history with automatic summarization.
    """

    messages: list[dict[str, str]] = Field(
        default_factory=list, description="List of messages (role, content)"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens in window")
    current_tokens: int = Field(default=0, description="Current token count")
    summary: str | None = Field(None, description="Summary of old context")


class MemoryStats(BaseModel):
    """Statistics about the memory graph."""

    total_memories: int = Field(..., description="Total number of memories")
    memory_types: dict[str, int] = Field(..., description="Count by type")
    total_chunks: int = Field(..., description="Total number of chunks")
    embedding_models: dict[str, int] = Field(..., description="Count by embedding model")
    storage_size_mb: float = Field(..., description="Storage size in MB")
    oldest_memory: datetime | None = Field(None, description="Oldest memory timestamp")
    newest_memory: datetime | None = Field(None, description="Newest memory timestamp")
    qdrant_available: bool = Field(..., description="Whether Qdrant is available")


class StoreRequest(BaseModel):
    """Request to store a memory."""

    content: str = Field(..., min_length=1, description="Content to store")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    memory_type: MemoryType = Field(default=MemoryType.NOTE, description="Type of memory")


class RecallRequest(BaseModel):
    """Request to recall memories."""

    query: str = Field(..., min_length=1, description="Search query")
    k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    memory_type: MemoryType | None = Field(None, description="Filter by memory type")


class UpdateRequest(BaseModel):
    """Request to update a memory."""

    content: str | None = Field(None, description="New content")
    metadata: dict[str, Any] | None = Field(None, description="New metadata")
    memory_type: MemoryType | None = Field(None, description="New memory type")


class MemoryConfig(BaseModel):
    """Configuration for Memory module."""

    db_path: str = Field(default="data/memory.db", description="SQLite database path")
    qdrant_path: str = Field(default="data/qdrant", description="Qdrant storage path")
    embedding_model: str = Field(default="mxbai-embed-large", description="Ollama embedding model")
    embedding_dimension: int = Field(default=1024, description="Embedding vector dimension")
    context_window_size: int = Field(default=4096, description="Max context window tokens")
    chunk_size: int = Field(default=500, description="Max chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    fts_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="FTS5 weight in hybrid search"
    )
    semantic_weight: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Semantic weight in hybrid search"
    )
    rrf_k: int = Field(default=60, description="Reciprocal Rank Fusion constant")
