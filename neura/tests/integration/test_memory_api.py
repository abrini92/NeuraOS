"""
Integration tests for Memory API endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app
from neura.core.types import Result
from neura.memory.types import MemoryEntry, MemoryStats, MemoryType


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestMemoryEndpoints:
    """Test Memory API endpoints."""

    @patch("neura.memory.router.get_memory_graph")
    def test_memory_info(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/ endpoint."""
        response = client.get("/api/memory/")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "memory"
        assert data["status"] == "operational"
        assert "endpoints" in data

    @patch("neura.memory.router.get_memory_graph")
    def test_store_memory(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/store endpoint."""
        # Mock memory graph
        mock_instance = AsyncMock()
        mock_entry = MemoryEntry(
            id="mem_123",
            content="Neura is a cognitive OS",
            content_hash="abc123",
            metadata={"type": "note"},
            memory_type=MemoryType.NOTE,
        )
        mock_instance.store.return_value = Result.success(mock_entry)
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.post(
            "/api/memory/store",
            json={
                "content": "Neura is a cognitive OS",
                "metadata": {"type": "note"},
                "memory_type": "note",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mem_123"
        assert data["content"] == "Neura is a cognitive OS"

    @patch("neura.memory.router.get_memory_graph")
    def test_store_memory_failure(self, mock_graph, client: TestClient) -> None:
        """Test store endpoint error handling."""
        # Mock failure
        mock_instance = AsyncMock()
        mock_instance.store.return_value = Result.failure("Database error")
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.post(
            "/api/memory/store",
            json={"content": "Test"},
        )

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    @patch("neura.memory.router.get_memory_graph")
    def test_recall_memories(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/recall endpoint."""
        # Mock memory graph
        from neura.memory.types import RecallResult

        mock_instance = AsyncMock()
        mock_entry = MemoryEntry(
            id="mem_456",
            content="Local-first architecture",
            content_hash="def456",
            metadata={},
        )
        mock_results = [
            RecallResult(entry=mock_entry, score=0.95, source="hybrid")
        ]
        mock_instance.recall.return_value = mock_results
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.post(
            "/api/memory/recall",
            json={"query": "local-first", "k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entry"]["id"] == "mem_456"
        assert data[0]["score"] == 0.95
        assert data[0]["source"] == "hybrid"

    @patch("neura.memory.router.get_memory_graph")
    def test_get_memory_by_id(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/{memory_id} endpoint."""
        mock_instance = AsyncMock()
        mock_entry = MemoryEntry(
            id="mem_789",
            content="Test memory",
            content_hash="ghi789",
            metadata={},
        )
        mock_instance.get_by_id.return_value = mock_entry
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.get("/api/memory/mem_789")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mem_789"
        assert data["content"] == "Test memory"

    @patch("neura.memory.router.get_memory_graph")
    def test_get_memory_not_found(self, mock_graph, client: TestClient) -> None:
        """Test getting non-existent memory."""
        mock_instance = AsyncMock()
        mock_instance.get_by_id.return_value = None
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.get("/api/memory/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("neura.memory.router.get_memory_graph")
    def test_delete_memory(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/{memory_id} DELETE endpoint."""
        mock_instance = AsyncMock()
        mock_instance.delete.return_value = Result.success(True)
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.delete("/api/memory/mem_123")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    @patch("neura.memory.router.get_memory_graph")
    def test_delete_memory_failure(self, mock_graph, client: TestClient) -> None:
        """Test delete endpoint error handling."""
        mock_instance = AsyncMock()
        mock_instance.delete.return_value = Result.failure("Memory not found")
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.delete("/api/memory/nonexistent")

        assert response.status_code == 500
        assert "Memory not found" in response.json()["detail"]

    @patch("neura.memory.router.get_memory_graph")
    def test_get_stats(self, mock_graph, client: TestClient) -> None:
        """Test /api/memory/stats endpoint."""
        mock_instance = AsyncMock()
        mock_stats = MemoryStats(
            total_memories=42,
            memory_types={"note": 30, "conversation": 12},
            total_chunks=45,
            embedding_models={"mxbai-embed-large": 42},
            storage_size_mb=12.5,
            qdrant_available=True,
        )
        mock_instance.get_stats.return_value = mock_stats
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.get("/api/memory/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_memories"] == 42
        assert data["storage_size_mb"] == 12.5
        assert data["qdrant_available"] is True

    def test_invalid_recall_request(self, client: TestClient) -> None:
        """Test recall with invalid parameters."""
        response = client.post(
            "/api/memory/recall",
            json={"query": "", "k": 5},  # Empty query
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_store_request(self, client: TestClient) -> None:
        """Test store with invalid parameters."""
        response = client.post(
            "/api/memory/store",
            json={"content": ""},  # Empty content
        )

        assert response.status_code == 422  # Validation error


class TestGracefulDegradation:
    """Test graceful degradation when services are unavailable."""

    @patch("neura.memory.router.get_memory_graph")
    def test_store_with_qdrant_unavailable(self, mock_graph, client: TestClient) -> None:
        """Test storing when Qdrant is unavailable (degraded mode)."""
        mock_instance = AsyncMock()
        mock_instance._qdrant_available = False  # Qdrant down
        mock_entry = MemoryEntry(
            id="mem_degraded",
            content="Test in degraded mode",
            content_hash="degraded123",
            metadata={},
        )
        mock_instance.store.return_value = Result.success(mock_entry)
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.post(
            "/api/memory/store",
            json={"content": "Test in degraded mode"},
        )

        # Should still succeed (graceful degradation)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test in degraded mode"

    @patch("neura.memory.router.get_memory_graph")
    def test_recall_fts_only_mode(self, mock_graph, client: TestClient) -> None:
        """Test recall using FTS only when Qdrant unavailable."""
        from neura.memory.types import RecallResult

        mock_instance = AsyncMock()
        mock_instance._qdrant_available = False
        mock_entry = MemoryEntry(
            id="mem_fts",
            content="FTS only result",
            content_hash="fts123",
            metadata={},
        )
        mock_results = [
            RecallResult(entry=mock_entry, score=0.8, source="fts")
        ]
        mock_instance.recall.return_value = mock_results
        mock_instance._initialized = True
        mock_graph.return_value = mock_instance

        response = client.post(
            "/api/memory/recall",
            json={"query": "test", "k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "fts"  # FTS only
