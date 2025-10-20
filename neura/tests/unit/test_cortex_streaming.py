"""
Unit tests for Cortex streaming functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from neura.cortex.engine import OllamaClient
from neura.cortex.types import CortexConfig, GenerateRequest


class TestCortexStreaming:
    """Test streaming text generation."""

    @pytest.fixture
    def config(self) -> CortexConfig:
        """Create test config."""
        return CortexConfig(
            ollama_host="http://localhost:11434",
            default_model="mistral",
        )

    @pytest.fixture
    def client(self, config: CortexConfig) -> OllamaClient:
        """Create test client."""
        return OllamaClient(config)

    @pytest.mark.asyncio
    async def test_generate_stream_success(self, client: OllamaClient) -> None:
        """Test successful streaming generation."""
        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        # Simulate streaming chunks
        chunks = [
            '{"response": "Hello", "done": false}',
            '{"response": " world", "done": false}',
            '{"response": "!", "done": true}',
        ]
        
        async def mock_aiter_lines():
            for chunk in chunks:
                yield chunk
        
        mock_response.aiter_lines = mock_aiter_lines
        
        # Mock stream context manager
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        mock_stream.__aexit__.return_value = None
        
        with patch.object(client._client, 'stream', return_value=mock_stream):
            request = GenerateRequest(prompt="Test prompt")
            
            # Collect streamed chunks
            result_chunks = []
            async for chunk in client.generate_stream(request):
                if chunk.is_success():
                    result_chunks.append(chunk.data)
            
            # Verify
            assert len(result_chunks) == 3
            assert result_chunks == ["Hello", " world", "!"]
            assert "".join(result_chunks) == "Hello world!"

    @pytest.mark.asyncio
    async def test_generate_stream_with_context(self, client: OllamaClient) -> None:
        """Test streaming with context."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        chunks = ['{"response": "Answer", "done": true}']
        
        async def mock_aiter_lines():
            for chunk in chunks:
                yield chunk
        
        mock_response.aiter_lines = mock_aiter_lines
        
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        mock_stream.__aexit__.return_value = None
        
        with patch.object(client._client, 'stream', return_value=mock_stream):
            request = GenerateRequest(
                prompt="Question?",
                context=["Context 1", "Context 2"]
            )
            
            chunks_received = []
            async for chunk in client.generate_stream(request):
                if chunk.is_success():
                    chunks_received.append(chunk.data)
            
            assert len(chunks_received) > 0

    @pytest.mark.asyncio
    async def test_generate_stream_error(self, client: OllamaClient) -> None:
        """Test streaming error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        mock_stream.__aexit__.return_value = None
        
        with patch.object(client._client, 'stream', return_value=mock_stream):
            request = GenerateRequest(prompt="Test")
            
            # Should yield error
            async for chunk in client.generate_stream(request):
                assert chunk.is_failure()
                assert "error" in chunk.error.lower()
                break

    @pytest.mark.asyncio
    async def test_generate_vs_generate_stream(self, client: OllamaClient) -> None:
        """Test that both methods work."""
        # Mock non-streaming
        mock_response_normal = MagicMock()
        mock_response_normal.status_code = 200
        mock_response_normal.json.return_value = {
            "response": "Complete response",
            "done": True
        }
        
        with patch.object(client._client, 'post', return_value=mock_response_normal):
            request = GenerateRequest(prompt="Test")
            result = await client.generate(request)
            
            assert result.is_success()
            assert "Complete response" in result.data.text
        
        # Mock streaming
        mock_response_stream = AsyncMock()
        mock_response_stream.status_code = 200
        
        async def mock_aiter():
            yield '{"response": "Streamed", "done": false}'
            yield '{"response": " response", "done": true}'
        
        mock_response_stream.aiter_lines = mock_aiter
        
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response_stream
        mock_stream.__aexit__.return_value = None
        
        with patch.object(client._client, 'stream', return_value=mock_stream):
            chunks = []
            async for chunk in client.generate_stream(request):
                if chunk.is_success():
                    chunks.append(chunk.data)
            
            assert len(chunks) == 2
            assert "".join(chunks) == "Streamed response"
