"""
Memory API router - FastAPI endpoints for memory operations.

Provides REST endpoints for storing, recalling, and managing memories.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from neura.core.config import get_settings
from neura.memory.graph import get_memory_graph
from neura.memory.types import (
    MemoryEntry,
    MemoryStats,
    RecallRequest,
    RecallResult,
    StoreRequest,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# WHY Journal path
WHY_JOURNAL_PATH = Path("data/why_journal.jsonl")


def log_to_why_journal(
    actor: str,
    action: str,
    input_summary: str,
    result: str,
    trace_id: str,
) -> None:
    """
    Log to WHY Journal for audit trail.

    Args:
        actor: Who performed the action
        action: What action was performed
        input_summary: Summary of input (max 200 chars)
        result: SUCCESS or FAILURE
        trace_id: Trace ID for correlation
    """
    WHY_JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor,
        "action": action,
        "input_summary": input_summary[:200],
        "policy_check": "PASS",
        "user_approved": True,
        "result": result,
        "trace_id": trace_id,
    }

    with open(WHY_JOURNAL_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    logger.debug(f"WHY Journal: {action} - {result}")


@router.post("/store", response_model=MemoryEntry)
async def store_memory(request: StoreRequest) -> MemoryEntry:
    """
    Store a memory in the graph.

    Args:
        request: Store request with content and metadata

    Returns:
        MemoryEntry: Stored memory

    Raises:
        HTTPException: If storage fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/memory/store \
          -H "Content-Type: application/json" \
          -d '{
            "content": "Neura is a local-first cognitive OS",
            "metadata": {"type": "note"}
          }'
        ```
    """
    trace_id = str(uuid.uuid4())
    logger.info(
        f"[{trace_id}] Store request: length={len(request.content)}, type={request.memory_type}"
    )

    # Initialize graph if needed
    settings = get_settings()
    graph = get_memory_graph(
        db_path=str(settings.memory_db_path),
        qdrant_path=str(settings.data_dir / "qdrant"),
        embedding_model=settings.embedding_model,
        embedding_dimension=1024,
        embedding_version="embed_v1",
    )

    if not graph._initialized:
        await graph.initialize()

    # Store memory
    result = await graph.store(
        content=request.content,
        metadata=request.metadata,
        memory_type=request.memory_type,
    )

    if result.is_failure():
        logger.error(f"[{trace_id}] Store failed: {result.error}")
        log_to_why_journal(
            actor="memory",
            action="store_memory",
            input_summary=request.content,
            result="FAILURE",
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail=result.error)

    # Log to WHY Journal
    log_to_why_journal(
        actor="memory",
        action="store_memory",
        input_summary=request.content,
        result="SUCCESS",
        trace_id=trace_id,
    )

    return result.data


@router.post("/recall", response_model=list[RecallResult])
async def recall_memories(request: RecallRequest) -> list[RecallResult]:
    """
    Recall memories using hybrid search.

    Args:
        request: Recall request with query and parameters

    Returns:
        List[RecallResult]: Top k memories ranked by relevance

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/memory/recall \
          -H "Content-Type: application/json" \
          -d '{"query": "cognitive OS", "k": 5}'
        ```
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] Recall request: query='{request.query}', k={request.k}")

    # Initialize graph if needed
    settings = get_settings()
    graph = get_memory_graph(
        db_path=str(settings.memory_db_path),
        qdrant_path=str(settings.data_dir / "qdrant"),
    )

    if not graph._initialized:
        await graph.initialize()

    # Recall memories
    results = await graph.recall(
        query=request.query,
        k=request.k,
        memory_type=request.memory_type,
    )

    logger.info(f"[{trace_id}] Recalled {len(results)} memories")
    return results


@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats() -> MemoryStats:
    """
    Get memory graph statistics.

    Returns:
        MemoryStats: Statistics about stored memories

    Example:
        ```bash
        curl http://localhost:8000/api/memory/stats
        ```
    """
    logger.debug("Stats request")

    settings = get_settings()
    graph = get_memory_graph(
        db_path=str(settings.memory_db_path),
        qdrant_path=str(settings.data_dir / "qdrant"),
    )

    if not graph._initialized:
        await graph.initialize()

    stats = await graph.get_stats()
    return stats


@router.get("/{memory_id}", response_model=MemoryEntry)
async def get_memory(memory_id: str) -> MemoryEntry:
    """
    Get a specific memory by ID.

    Args:
        memory_id: Memory ID

    Returns:
        MemoryEntry: The memory

    Raises:
        HTTPException: If memory not found
    """
    logger.debug(f"Get memory: {memory_id}")

    settings = get_settings()
    graph = get_memory_graph(
        db_path=str(settings.memory_db_path),
        qdrant_path=str(settings.data_dir / "qdrant"),
    )

    if not graph._initialized:
        await graph.initialize()

    memory = await graph.get_by_id(memory_id)

    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

    return memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str) -> dict:
    """
    Delete a memory by ID.

    Args:
        memory_id: Memory ID

    Returns:
        dict: Success message

    Raises:
        HTTPException: If deletion fails
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] Delete memory: {memory_id}")

    settings = get_settings()
    graph = get_memory_graph(
        db_path=str(settings.memory_db_path),
        qdrant_path=str(settings.data_dir / "qdrant"),
    )

    if not graph._initialized:
        await graph.initialize()

    result = await graph.delete(memory_id)

    if result.is_failure():
        logger.error(f"[{trace_id}] Delete failed: {result.error}")
        log_to_why_journal(
            actor="memory",
            action="delete_memory",
            input_summary=f"memory_id={memory_id}",
            result="FAILURE",
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail=result.error)

    # Log to WHY Journal
    log_to_why_journal(
        actor="memory",
        action="delete_memory",
        input_summary=f"memory_id={memory_id}",
        result="SUCCESS",
        trace_id=trace_id,
    )

    return {"message": f"Memory {memory_id} deleted successfully"}


@router.get("/")
async def memory_info() -> dict:
    """
    Get Memory module information.

    Returns:
        dict: Module information
    """
    return {
        "module": "memory",
        "status": "operational",
        "description": "Persistent memory graph with hybrid search",
        "endpoints": {
            "store": "/api/memory/store",
            "recall": "/api/memory/recall",
            "stats": "/api/memory/stats",
            "get": "/api/memory/{memory_id}",
            "delete": "/api/memory/{memory_id}",
        },
    }
