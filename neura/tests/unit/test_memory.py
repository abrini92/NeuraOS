"""
Unit tests for Memory module.

Tests Memory Graph, Embeddings, and Context Manager with mocked dependencies.
"""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from neura.core.types import Result
from neura.memory.context_manager import ContextManager
from neura.memory.embeddings import EmbeddingEngine
from neura.memory.graph import MemoryGraph
from neura.memory.types import MemoryEntry, MemoryType


class TestEmbeddingEngine:
    """Test EmbeddingEngine class."""

    @pytest.mark.asyncio
    async def test_embed_success(self) -> None:
        """Test successful embedding generation."""
        engine = EmbeddingEngine(model="test-model", dimension=128)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 128}

        with patch.object(engine._client, "post", return_value=mock_response):
            result = await engine.embed("Test text")

            assert result.is_success()
            assert len(result.data) == 128
            assert all(isinstance(x, float) for x in result.data)

    @pytest.mark.asyncio
    async def test_embed_empty_text(self) -> None:
        """Test embedding empty text fails."""
        engine = EmbeddingEngine()

        result = await engine.embed("")
        assert result.is_failure()
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_embed_connection_error(self) -> None:
        """Test handling of connection errors."""
        from httpx import ConnectError

        engine = EmbeddingEngine()

        with patch.object(
            engine._client,
            "post",
            side_effect=ConnectError("Connection refused"),
        ):
            result = await engine.embed("Test")

            assert result.is_failure()
            assert "connect" in result.error.lower()

    @pytest.mark.asyncio
    async def test_batch_embed(self) -> None:
        """Test batch embedding."""
        engine = EmbeddingEngine(dimension=128)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 128}

        with patch.object(engine._client, "post", return_value=mock_response):
            texts = ["Text 1", "Text 2", "Text 3"]
            result = await engine.batch_embed(texts)

            assert result.is_success()
            assert len(result.data) == 3
            assert all(e is not None for e in result.data)


class TestMemoryGraph:
    """Test MemoryGraph class."""

    @pytest.fixture
    async def memory_graph(self, tmp_path) -> MemoryGraph:
        """Create a test memory graph."""
        graph = MemoryGraph(
            db_path=str(tmp_path / "test_memory.db"),
            qdrant_path=str(tmp_path / "test_qdrant"),
            embedding_model="test-model",
            embedding_dimension=128,
        )
        await graph.initialize()
        return graph

    @pytest.mark.asyncio
    async def test_store_memory(self, memory_graph: MemoryGraph) -> None:
        """Test storing a memory."""
        # Mock embedding engine
        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = Result.success([0.1] * 128)
        memory_graph._embedding_engine = mock_embedding

        # Mock Qdrant
        memory_graph._qdrant = AsyncMock()
        memory_graph._qdrant_available = True

        result = await memory_graph.store(
            content="Test memory content",
            metadata={"test": "value"},
            memory_type=MemoryType.NOTE,
        )

        assert result.is_success()
        assert result.data.content == "Test memory content"
        assert result.data.metadata["test"] == "value"
        assert result.data.memory_type == MemoryType.NOTE

    @pytest.mark.asyncio
    async def test_store_deduplication(self, memory_graph: MemoryGraph) -> None:
        """Test content deduplication."""
        # Mock embedding
        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = Result.success([0.1] * 128)
        memory_graph._embedding_engine = mock_embedding

        content = "Duplicate content"

        # Store first time
        result1 = await memory_graph.store(content)
        assert result1.is_success()
        id1 = result1.data.id

        # Store second time (should deduplicate)
        result2 = await memory_graph.store(content)
        assert result2.is_success()
        assert result2.data.id == id1  # Same ID (deduplicated)

    @pytest.mark.asyncio
    async def test_chunking(self, memory_graph: MemoryGraph) -> None:
        """Test content chunking."""
        long_content = "A" * 1000  # Exceeds chunk_size of 500

        chunks = memory_graph._chunk_content(long_content)

        assert len(chunks) > 1
        assert all(len(chunk) <= memory_graph.chunk_size + memory_graph.chunk_overlap for chunk in chunks)

    @pytest.mark.asyncio
    async def test_get_by_hash(self, memory_graph: MemoryGraph) -> None:
        """Test retrieving memory by hash."""
        # Mock embedding
        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = Result.success([0.1] * 128)
        memory_graph._embedding_engine = mock_embedding

        content = "Test content for hash"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Store
        await memory_graph.store(content)

        # Retrieve by hash
        entry = await memory_graph.get_by_hash(content_hash)
        assert entry is not None
        assert entry.content == content

    @pytest.mark.asyncio
    async def test_recall_fts_only(self, memory_graph: MemoryGraph) -> None:
        """Test recall with FTS only (Qdrant unavailable)."""
        # Disable Qdrant
        memory_graph._qdrant_available = False

        # Store some memories
        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = Result.success([0.1] * 128)
        memory_graph._embedding_engine = mock_embedding

        await memory_graph.store("Neura is a cognitive OS")
        await memory_graph.store("Python is a programming language")

        # Recall
        results = await memory_graph.recall("cognitive", k=5)

        assert len(results) > 0
        assert results[0].source == "fts"

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_graph: MemoryGraph) -> None:
        """Test deleting a memory."""
        # Mock embedding
        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = Result.success([0.1] * 128)
        memory_graph._embedding_engine = mock_embedding

        # Store
        result = await memory_graph.store("Memory to delete")
        memory_id = result.data.id

        # Delete
        delete_result = await memory_graph.delete(memory_id)
        assert delete_result.is_success()

        # Verify deleted
        entry = await memory_graph.get_by_id(memory_id)
        assert entry is None

    @pytest.mark.asyncio
    async def test_rrf_fusion(self, memory_graph: MemoryGraph) -> None:
        """Test Reciprocal Rank Fusion."""
        # Create mock entries
        entry1 = MemoryEntry(
            id="mem1",
            content="Test 1",
            content_hash="hash1",
            metadata={},
        )
        entry2 = MemoryEntry(
            id="mem2",
            content="Test 2",
            content_hash="hash2",
            metadata={},
        )

        # entry1: rank 0 in fts, rank 2 in semantic → 1/(0+60) + 1/(2+60) = 0.0167 + 0.0161 = 0.0328
        # entry2: rank 1 in fts, rank 0 in semantic → 1/(1+60) + 1/(0+60) = 0.0164 + 0.0167 = 0.0331
        # entry3: rank 2 in fts only → 1/(2+60) = 0.0161
        entry3 = MemoryEntry(
            id="mem3",
            content="Test 3",
            content_hash="hash3",
            metadata={},
        )

        fts_results = [(entry1, 0.9), (entry2, 0.8), (entry3, 0.7)]
        semantic_results = [(entry2, 0.95), (entry3, 0.9), (entry1, 0.7)]

        combined = memory_graph._reciprocal_rank_fusion(fts_results, semantic_results)

        assert len(combined) == 3
        # Entry2 should rank highest (best combined RRF score)
        assert combined[0][0].id == "mem2"


class TestContextManager:
    """Test ContextManager class."""

    def test_add_message(self) -> None:
        """Test adding messages to context."""
        manager = ContextManager(max_tokens=1000)

        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi there!")

        assert manager.get_message_count() == 2
        assert manager.get_token_count() > 0

    def test_get_context(self) -> None:
        """Test getting context."""
        manager = ContextManager(max_tokens=1000)

        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi!")
        manager.add_message("user", "How are you?")

        context = manager.get_context()

        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"

    def test_context_window_overflow(self) -> None:
        """Test context window overflow triggers summarization."""
        manager = ContextManager(max_tokens=100)

        # Add messages until overflow
        for i in range(10):
            manager.add_message("user", f"Message {i} " * 20)

        # Should have summarized
        assert manager.get_summary() is not None

    def test_clear_context(self) -> None:
        """Test clearing context."""
        manager = ContextManager()

        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi!")

        manager.clear()

        assert manager.get_message_count() == 0
        assert manager.get_token_count() == 0
        assert manager.get_summary() is None

    def test_export_import(self) -> None:
        """Test exporting and importing context."""
        manager1 = ContextManager()
        manager1.add_message("user", "Test")

        # Export
        exported = manager1.export()

        # Import to new manager
        manager2 = ContextManager()
        manager2.import_context(exported)

        assert manager2.get_message_count() == 1
        assert manager2.get_context()[0]["content"] == "Test"


class TestMemoryTypes:
    """Test memory types and validation."""

    def test_memory_entry_creation(self) -> None:
        """Test creating a memory entry."""
        entry = MemoryEntry(
            id="test_id",
            content="Test content",
            content_hash="abc123",
            metadata={"key": "value"},
            memory_type=MemoryType.NOTE,
        )

        assert entry.id == "test_id"
        assert entry.content == "Test content"
        assert entry.memory_type == MemoryType.NOTE

    def test_memory_type_enum(self) -> None:
        """Test memory type enumeration."""
        assert MemoryType.NOTE.value == "note"
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.OBSERVATION.value == "observation"
