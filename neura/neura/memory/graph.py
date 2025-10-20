"""
Memory graph - Persistent storage with hybrid search.

Combines SQLite FTS5 (full-text search) with Qdrant (semantic search)
for optimal memory recall with Reciprocal Rank Fusion.
"""

import hashlib
import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from neura.core.events import get_event_bus
from neura.core.types import Result
from neura.memory.embeddings import EmbeddingEngine, get_embedding_engine
from neura.memory.types import ChunkMetadata, MemoryEntry, MemoryStats, MemoryType, RecallResult

logger = logging.getLogger(__name__)


class MemoryGraph:
    """
    Persistent memory graph with hybrid search.

    Combines full-text search (SQLite FTS5) with semantic search (Qdrant)
    for optimal recall using Reciprocal Rank Fusion.

    Example:
        >>> graph = MemoryGraph(db_path="data/memory.db")
        >>> await graph.initialize()
        >>> result = await graph.store("Neura is a cognitive OS")
        >>> memories = await graph.recall("cognitive system", k=5)
    """

    def __init__(
        self,
        db_path: str = "data/memory.db",
        qdrant_path: str = "data/qdrant",
        embedding_model: str = "mxbai-embed-large",
        embedding_dimension: int = 1024,
        embedding_version: str = "embed_v1",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        rrf_k: int = 60,
    ) -> None:
        """
        Initialize memory graph.

        Args:
            db_path: Path to SQLite database
            qdrant_path: Path to Qdrant storage
            embedding_model: Model for embeddings
            embedding_dimension: Embedding vector dimension
            embedding_version: Version for migration tracking
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
            rrf_k: Reciprocal Rank Fusion constant
        """
        self.db_path = Path(db_path)
        self.qdrant_path = Path(qdrant_path)
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.embedding_version = embedding_version
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.rrf_k = rrf_k

        self._conn: sqlite3.Connection | None = None
        self._qdrant: AsyncQdrantClient | None = None
        self._embedding_engine: EmbeddingEngine | None = None
        self._qdrant_available = False
        self._initialized = False

        logger.info(f"MemoryGraph created: db={db_path}, version={embedding_version}")

    async def initialize(self) -> None:
        """
        Initialize the memory graph.

        Creates SQLite tables, Qdrant collection, and embedding engine.
        """
        if self._initialized:
            logger.warning("MemoryGraph already initialized")
            return

        start_time = datetime.utcnow()

        # Create directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.qdrant_path.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite
        await self._init_sqlite()

        # Initialize Qdrant (graceful degradation if fails)
        await self._init_qdrant()

        # Initialize embedding engine
        self._embedding_engine = get_embedding_engine(
            model=self.embedding_model,
            dimension=self.embedding_dimension,
            version=self.embedding_version,
        )

        self._initialized = True

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"MemoryGraph initialized in {duration:.0f}ms")

        if duration > 1000:
            logger.warning(f"Initialization took {duration:.0f}ms (target: <500ms)")

    async def _init_sqlite(self) -> None:
        """Initialize SQLite database with FTS5."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

        # Create main table
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                metadata JSON,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                embedding_model TEXT,
                embedding_version TEXT
            )
        """
        )

        # Create FTS5 virtual table
        self._conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                content,
                content='memories',
                content_rowid='rowid'
            )
        """
        )

        # Create triggers to keep FTS in sync
        self._conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, id, content)
                VALUES (new.rowid, new.id, new.content);
            END
        """
        )

        self._conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                UPDATE memories_fts
                SET content = new.content
                WHERE rowid = new.rowid;
            END
        """
        )

        self._conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.rowid;
            END
        """
        )

        self._conn.commit()
        logger.info("SQLite initialized with FTS5")

    async def _init_qdrant(self) -> None:
        """Initialize Qdrant vector database (embedded mode)."""
        try:
            self._qdrant = AsyncQdrantClient(path=str(self.qdrant_path))

            # Create collection if not exists
            collections = await self._qdrant.get_collections()
            collection_names = [c.name for c in collections.collections]

            if "memories" not in collection_names:
                await self._qdrant.create_collection(
                    collection_name="memories",
                    vectors_config=qdrant_models.VectorParams(
                        size=self.embedding_dimension,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: dim={self.embedding_dimension}")

            self._qdrant_available = True
            logger.info("Qdrant initialized (embedded mode)")

        except Exception as e:
            logger.warning(f"Qdrant initialization failed: {e}")
            logger.warning("Running in degraded mode (FTS5 only)")
            self._qdrant_available = False

    async def store(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        memory_type: MemoryType = MemoryType.NOTE,
    ) -> Result[MemoryEntry]:
        """
        Store content in memory graph with deduplication.

        Args:
            content: Content to store
            metadata: Optional metadata
            memory_type: Type of memory

        Returns:
            Result[MemoryEntry]: Stored memory entry or error

        Example:
            >>> result = await graph.store("Neura is local-first")
            >>> if result.is_success():
            ...     print(f"Stored: {result.data.id}")
        """
        if not self._initialized:
            return Result.failure("MemoryGraph not initialized")

        start_time = datetime.utcnow()

        try:
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Check if already exists
            existing = await self.get_by_hash(content_hash)
            if existing:
                logger.info(f"Content already stored: {content_hash[:8]}")
                # Update timestamp
                self._conn.execute(
                    "UPDATE memories SET timestamp = CURRENT_TIMESTAMP WHERE content_hash = ?",
                    (content_hash,),
                )
                self._conn.commit()
                return Result.success(existing)

            # Generate ID
            memory_id = f"mem_{uuid.uuid4().hex[:12]}"

            # Chunk content if necessary
            chunks = self._chunk_content(content) if len(content) > self.chunk_size else [content]

            # Store chunks
            for i, chunk in enumerate(chunks):
                chunk_id = f"{memory_id}_chunk{i}" if len(chunks) > 1 else memory_id
                chunk_metadata = metadata or {}

                if len(chunks) > 1:
                    chunk_metadata["chunk"] = ChunkMetadata(
                        parent_id=memory_id,
                        chunk_index=i,
                        total_chunks=len(chunks),
                    ).dict()

                # Store in SQLite
                self._conn.execute(
                    """
                    INSERT INTO memories (id, content, content_hash, metadata, type, embedding_model, embedding_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        chunk,
                        content_hash if i == 0 else hashlib.sha256(chunk.encode()).hexdigest(),
                        json.dumps(chunk_metadata),
                        memory_type.value,
                        self.embedding_model,
                        self.embedding_version,
                    ),
                )

                # Generate and store embedding (if Qdrant available)
                if self._qdrant_available and self._embedding_engine:
                    embedding_result = await self._embedding_engine.embed(chunk)

                    if embedding_result.is_success():
                        try:
                            await self._qdrant.upsert(
                                collection_name="memories",
                                points=[
                                    qdrant_models.PointStruct(
                                        id=chunk_id,
                                        vector=embedding_result.data,
                                        payload={
                                            "content": chunk,
                                            "memory_id": memory_id,
                                            "type": memory_type.value,
                                        },
                                    )
                                ],
                            )
                        except Exception as e:
                            logger.warning(f"Failed to store embedding in Qdrant: {e}")
                    else:
                        logger.warning(f"Failed to generate embedding: {embedding_result.error}")

            self._conn.commit()

            # Create entry object
            entry = MemoryEntry(
                id=memory_id,
                content=content,
                content_hash=content_hash,
                metadata=metadata or {},
                timestamp=datetime.utcnow(),
                memory_type=memory_type,
                embedding_model=self.embedding_model,
            )

            # Publish event
            event_bus = get_event_bus()
            await event_bus.publish(
                "memory.stored",
                {
                    "id": entry.id,
                    "type": entry.memory_type.value,
                    "chunks": len(chunks),
                    "embedding_version": self.embedding_version,
                },
                source="memory",
            )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Stored memory {memory_id} ({len(chunks)} chunks) in {duration:.0f}ms")

            if duration > 400:
                logger.warning(f"Store operation took {duration:.0f}ms (target: <200ms)")

            return Result.success(entry)

        except sqlite3.IntegrityError as e:
            error_msg = f"Database integrity error: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

        except Exception as e:
            error_msg = f"Failed to store memory: {e}"
            logger.error(error_msg, exc_info=True)
            return Result.failure(error_msg)

    async def recall(
        self,
        query: str,
        k: int = 5,
        memory_type: MemoryType | None = None,
    ) -> list[RecallResult]:
        """
        Recall memories using hybrid search (FTS5 + Qdrant + RRF).

        Args:
            query: Search query
            k: Number of results to return
            memory_type: Optional filter by type

        Returns:
            List[RecallResult]: Top k memories ranked by relevance

        Example:
            >>> results = await graph.recall("cognitive OS", k=5)
            >>> for result in results:
            ...     print(f"{result.score:.2f}: {result.entry.content[:50]}")
        """
        if not self._initialized:
            logger.error("MemoryGraph not initialized")
            return []

        start_time = datetime.utcnow()

        try:
            # 1. FTS5 full-text search
            fts_results = await self._fts_search(query, limit=20, memory_type=memory_type)

            # 2. Semantic search via Qdrant (if available)
            semantic_results = []
            if self._qdrant_available and self._embedding_engine:
                semantic_results = await self._semantic_search(
                    query, limit=20, memory_type=memory_type
                )

            # 3. Combine with Reciprocal Rank Fusion
            if semantic_results:
                combined = self._reciprocal_rank_fusion(fts_results, semantic_results)
            else:
                # Fallback to FTS only if Qdrant unavailable
                logger.debug("Using FTS5 only (Qdrant unavailable)")
                combined = [(entry, score, "fts") for entry, score in fts_results]

            # 4. Return top K
            top_k = combined[:k]
            results = [
                RecallResult(entry=entry, score=score, source=source)
                for entry, score, source in top_k
            ]

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Recalled {len(results)} memories in {duration:.0f}ms")

            if duration > 200:
                logger.warning(f"Recall operation took {duration:.0f}ms (target: <100ms)")

            return results

        except Exception as e:
            logger.error(f"Recall failed: {e}", exc_info=True)
            return []

    async def _fts_search(
        self,
        query: str,
        limit: int = 20,
        memory_type: MemoryType | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """Full-text search using SQLite FTS5."""
        try:
            type_filter = f"AND type = '{memory_type.value}'" if memory_type else ""

            cursor = self._conn.execute(
                f"""
                SELECT m.*, rank
                FROM memories_fts
                JOIN memories m ON memories_fts.rowid = m.rowid
                WHERE memories_fts MATCH ?
                {type_filter}
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            )

            results = []
            for row in cursor.fetchall():
                entry = self._row_to_entry(row)
                # Convert BM25 rank to 0-1 score (negative rank, normalize)
                score = 1.0 / (1.0 + abs(row["rank"]))
                results.append((entry, score))

            logger.debug(f"FTS5 search: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"FTS search failed: {e}")
            return []

    async def _semantic_search(
        self,
        query: str,
        limit: int = 20,
        memory_type: MemoryType | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """Semantic search using Qdrant."""
        try:
            # Generate query embedding
            embedding_result = await self._embedding_engine.embed(query)

            if embedding_result.is_failure():
                logger.warning(f"Failed to embed query: {embedding_result.error}")
                return []

            # Search Qdrant
            search_filter = None
            if memory_type:
                search_filter = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="type",
                            match=qdrant_models.MatchValue(value=memory_type.value),
                        )
                    ]
                )

            search_result = await self._qdrant.search(
                collection_name="memories",
                query_vector=embedding_result.data,
                limit=limit,
                query_filter=search_filter,
            )

            results = []
            for hit in search_result:
                # Fetch full entry from SQLite
                cursor = self._conn.execute(
                    "SELECT * FROM memories WHERE id = ?",
                    (hit.id,),
                )
                row = cursor.fetchone()
                if row:
                    entry = self._row_to_entry(row)
                    results.append((entry, hit.score))

            logger.debug(f"Semantic search: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        results1: list[tuple[MemoryEntry, float]],
        results2: list[tuple[MemoryEntry, float]],
    ) -> list[tuple[MemoryEntry, float, str]]:
        """
        Combine two result lists using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (rank + k))

        Args:
            results1: FTS5 results
            results2: Semantic results

        Returns:
            Combined and reranked results with source
        """
        scores: dict[str, float] = {}
        entries: dict[str, MemoryEntry] = {}

        # Process FTS results
        for rank, (entry, _) in enumerate(results1):
            rrf_score = 1.0 / (rank + self.rrf_k)
            scores[entry.id] = scores.get(entry.id, 0.0) + rrf_score
            entries[entry.id] = entry

        # Process semantic results
        for rank, (entry, _) in enumerate(results2):
            rrf_score = 1.0 / (rank + self.rrf_k)
            scores[entry.id] = scores.get(entry.id, 0.0) + rrf_score
            entries[entry.id] = entry

        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Determine source for each
        results = []
        for entry_id in sorted_ids:
            source = "hybrid"
            if entry_id in [e.id for e, _ in results1] and entry_id in [e.id for e, _ in results2]:
                source = "hybrid"
            elif entry_id in [e.id for e, _ in results1]:
                source = "fts"
            else:
                source = "semantic"

            results.append((entries[entry_id], scores[entry_id], source))

        logger.debug(f"RRF combined {len(results)} unique results")
        return results

    async def get_by_hash(self, content_hash: str) -> MemoryEntry | None:
        """
        Get memory by content hash.

        Args:
            content_hash: SHA256 hash of content

        Returns:
            MemoryEntry if found, None otherwise
        """
        cursor = self._conn.execute(
            "SELECT * FROM memories WHERE content_hash = ?",
            (content_hash,),
        )
        row = cursor.fetchone()
        return self._row_to_entry(row) if row else None

    async def get_by_id(self, memory_id: str) -> MemoryEntry | None:
        """Get memory by ID."""
        cursor = self._conn.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,),
        )
        row = cursor.fetchone()
        return self._row_to_entry(row) if row else None

    async def delete(self, memory_id: str) -> Result[bool]:
        """Delete a memory by ID."""
        try:
            # Delete from Qdrant if available
            if self._qdrant_available:
                try:
                    await self._qdrant.delete(
                        collection_name="memories",
                        points_selector=qdrant_models.PointIdsList(
                            points=[memory_id],
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete from Qdrant: {e}")

            # Delete from SQLite (triggers will handle FTS)
            self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self._conn.commit()

            logger.info(f"Deleted memory: {memory_id}")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Failed to delete memory: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def get_stats(self) -> MemoryStats:
        """Get memory graph statistics."""
        try:
            cursor = self._conn.execute("SELECT COUNT(*) as count FROM memories")
            total = cursor.fetchone()["count"]

            cursor = self._conn.execute(
                "SELECT type, COUNT(*) as count FROM memories GROUP BY type"
            )
            types = {row["type"]: row["count"] for row in cursor.fetchall()}

            cursor = self._conn.execute(
                "SELECT embedding_model, COUNT(*) as count FROM memories GROUP BY embedding_model"
            )
            models = {row["embedding_model"] or "none": row["count"] for row in cursor.fetchall()}

            # Storage size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0

            # Timestamps
            cursor = self._conn.execute(
                "SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM memories"
            )
            row = cursor.fetchone()
            oldest = datetime.fromisoformat(row["oldest"]) if row["oldest"] else None
            newest = datetime.fromisoformat(row["newest"]) if row["newest"] else None

            return MemoryStats(
                total_memories=total,
                memory_types=types,
                total_chunks=total,  # Simplified for now
                embedding_models=models,
                storage_size_mb=round(db_size_mb, 2),
                oldest_memory=oldest,
                newest_memory=newest,
                qdrant_available=self._qdrant_available,
            )

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return MemoryStats(
                total_memories=0,
                memory_types={},
                total_chunks=0,
                embedding_models={},
                storage_size_mb=0.0,
                qdrant_available=self._qdrant_available,
            )

    def _chunk_content(self, content: str) -> list[str]:
        """
        Chunk content intelligently with overlap.

        Args:
            content: Content to chunk

        Returns:
            List of chunks
        """
        if len(content) <= self.chunk_size:
            return [content]

        chunks = []

        # Try splitting by paragraphs first
        paragraphs = content.split("\n\n")

        # If no paragraphs or single long paragraph, do simple chunking
        if len(paragraphs) == 1 and len(paragraphs[0]) > self.chunk_size:
            # Simple chunking for long continuous text
            text = paragraphs[0]
            i = 0
            while i < len(text):
                chunk_end = min(i + self.chunk_size, len(text))
                chunks.append(text[i:chunk_end])
                i += self.chunk_size - self.chunk_overlap
            return chunks

        # Paragraph-based chunking
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        # Add overlap between chunks
        if len(chunks) > 1:
            overlapped = []
            for i, chunk in enumerate(chunks):
                if i > 0:
                    # Add overlap from previous chunk
                    prev = chunks[i - 1]
                    overlap = (
                        prev[-self.chunk_overlap :] if len(prev) > self.chunk_overlap else prev
                    )
                    chunk = overlap + " " + chunk
                overlapped.append(chunk)
            chunks = overlapped

        return chunks

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """Convert SQLite row to MemoryEntry."""
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            content_hash=row["content_hash"],
            metadata=metadata,
            timestamp=datetime.fromisoformat(row["timestamp"]),
            memory_type=MemoryType(row["type"]) if row["type"] else MemoryType.NOTE,
            embedding_model=row["embedding_model"],
        )

    async def close(self) -> None:
        """Close all connections."""
        if self._conn:
            self._conn.close()
        if self._qdrant:
            await self._qdrant.close()
        if self._embedding_engine:
            await self._embedding_engine.close()
        logger.info("MemoryGraph closed")


# Singleton instance
_memory_graph: MemoryGraph | None = None


def get_memory_graph(**kwargs) -> MemoryGraph:
    """Get the global memory graph instance."""
    global _memory_graph
    if _memory_graph is None:
        _memory_graph = MemoryGraph(**kwargs)
    return _memory_graph


async def close_memory_graph() -> None:
    """Close the global memory graph."""
    global _memory_graph
    if _memory_graph is not None:
        await _memory_graph.close()
        _memory_graph = None
