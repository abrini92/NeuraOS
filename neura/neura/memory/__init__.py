"""
Memory module - Persistent context and semantic search.

The Memory module provides:
- SQLite-based structured storage (FTS5)
- Qdrant vector embeddings for semantic search
- Memory graph for contextual relationships
- Long-term and short-term memory management
"""

from neura.memory.context_manager import ContextManager, get_context_manager
from neura.memory.embeddings import EmbeddingEngine, get_embedding_engine
from neura.memory.graph import MemoryGraph, get_memory_graph
from neura.memory.router import router
from neura.memory.types import (
    MemoryEntry,
    MemoryStats,
    MemoryType,
    RecallRequest,
    RecallResult,
    StoreRequest,
)

__all__ = [
    "MemoryGraph",
    "get_memory_graph",
    "EmbeddingEngine",
    "get_embedding_engine",
    "ContextManager",
    "get_context_manager",
    "router",
    "MemoryEntry",
    "MemoryStats",
    "MemoryType",
    "RecallRequest",
    "RecallResult",
    "StoreRequest",
]
