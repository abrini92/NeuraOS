"""
Embedding engine for semantic search.

Generates embeddings via Ollama with graceful degradation if unavailable.
"""

import logging

import httpx

from neura.core.types import Result

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Generate embeddings for semantic search.

    Supports multiple models via Ollama with automatic fallback.

    Example:
        >>> engine = EmbeddingEngine(model="mxbai-embed-large")
        >>> result = await engine.embed("Hello world")
        >>> if result.is_success():
        ...     print(f"Embedding dimension: {len(result.data)}")
    """

    def __init__(
        self,
        model: str = "mxbai-embed-large",
        ollama_host: str = "http://localhost:11434",
        dimension: int = 1024,
        version: str = "embed_v1",
        cache_size: int = 1000,
    ) -> None:
        """
        Initialize the embedding engine.

        Args:
            model: Ollama model to use for embeddings
            ollama_host: Ollama API host URL
            dimension: Expected embedding dimension
            version: Embedding version for migration tracking
            cache_size: Maximum number of embeddings to cache (default: 1000)
        """
        self.model = model
        self.ollama_host = ollama_host
        self.dimension = dimension
        self.version = version
        self._client = httpx.AsyncClient(timeout=30.0)
        self._degraded_mode = False
        
        # LRU Cache for embeddings
        self._cache: dict[str, list[float]] = {}
        self._cache_order: list[str] = []
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(
            f"EmbeddingEngine initialized: model={model}, version={version}, dim={dimension}"
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.debug("EmbeddingEngine closed")

    async def embed(self, text: str) -> Result[list[float]]:
        """
        Generate embedding for a single text (with caching).

        Args:
            text: Text to embed

        Returns:
            Result[List[float]]: Embedding vector or error

        Example:
            >>> result = await engine.embed("Neura is a cognitive OS")
            >>> if result.is_success():
            ...     embedding = result.data
        """
        if not text or not text.strip():
            return Result.failure("Cannot embed empty text")

        # Check cache first
        cache_key = f"{self.model}:{text}"
        if cache_key in self._cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit! (hits={self._cache_hits}, misses={self._cache_misses})")
            return Result.success(self._cache[cache_key])
        
        self._cache_misses += 1

        try:
            # Call Ollama embeddings API
            response = await self._client.post(
                f"{self.ollama_host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )

            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)

                # Try fallback if primary model fails
                if not self._degraded_mode:
                    logger.warning("Trying fallback model: mistral")
                    return await self._fallback_embed(text)

                return Result.failure(error_msg)

            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                return Result.failure("Empty embedding returned")

            if len(embedding) != self.dimension:
                logger.warning(
                    f"Unexpected embedding dimension: {len(embedding)} (expected {self.dimension})"
                )

            # Store in cache (LRU eviction)
            self._add_to_cache(cache_key, embedding)

            logger.debug(f"Generated embedding: dim={len(embedding)}")
            return Result.success(embedding)

        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to Ollama: {e}"
            logger.error(error_msg)

            # Try fallback
            if not self._degraded_mode:
                return await self._fallback_embed(text)

            return Result.failure(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error generating embedding: {e}"
            logger.error(error_msg, exc_info=True)
            return Result.failure(error_msg)

    async def batch_embed(self, texts: list[str]) -> Result[list[list[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Result[List[List[float]]]: List of embedding vectors or error

        Example:
            >>> texts = ["Hello", "World"]
            >>> result = await engine.batch_embed(texts)
            >>> if result.is_success():
            ...     embeddings = result.data
        """
        if not texts:
            return Result.failure("Cannot embed empty list")

        embeddings = []
        for i, text in enumerate(texts):
            result = await self.embed(text)

            if result.is_failure():
                logger.warning(f"Failed to embed text {i}: {result.error}")
                # Continue with None for failed embeddings
                embeddings.append(None)
            else:
                embeddings.append(result.data)

        # Check if at least some succeeded
        success_count = sum(1 for e in embeddings if e is not None)
        if success_count == 0:
            return Result.failure("All embeddings failed")

        logger.info(f"Batch embed: {success_count}/{len(texts)} successful")
        return Result.success(embeddings)

    async def _fallback_embed(self, text: str) -> Result[list[float]]:
        """
        Fallback embedding using Mistral model.

        This is less optimal but ensures degraded mode continues working.

        Args:
            text: Text to embed

        Returns:
            Result[List[float]]: Fallback embedding or error
        """
        try:
            logger.warning("Using fallback embedding model: mistral")
            self._degraded_mode = True

            response = await self._client.post(
                f"{self.ollama_host}/api/embeddings",
                json={"model": "mistral", "prompt": text},
            )

            if response.status_code != 200:
                error_msg = "Fallback model also failed"
                logger.error(error_msg)
                return Result.failure(error_msg)

            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                return Result.failure("Empty fallback embedding")

            logger.info(f"Fallback embedding generated: dim={len(embedding)}")
            return Result.success(embedding)

        except Exception as e:
            error_msg = f"Fallback embedding failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def check_availability(self) -> bool:
        """
        Check if the embedding model is available.

        Returns:
            bool: True if model is available
        """
        try:
            # Try a simple embedding
            result = await self.embed("test")
            return result.is_success()
        except Exception:
            return False

    def get_version(self) -> str:
        """Get the current embedding version."""
        return self.version
    
    def _add_to_cache(self, key: str, embedding: list[float]) -> None:
        """Add embedding to cache with LRU eviction."""
        # If key already exists, remove it from order list
        if key in self._cache:
            self._cache_order.remove(key)
        
        # Add to cache
        self._cache[key] = embedding
        self._cache_order.append(key)
        
        # Evict oldest if cache is full
        if len(self._cache) > self._cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key[:50]}...")
    
    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._cache_size,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0.0
        }


# Singleton instance
_embedding_engine: EmbeddingEngine | None = None


def get_embedding_engine(
    model: str = "mxbai-embed-large",
    ollama_host: str = "http://localhost:11434",
    dimension: int = 1024,
    version: str = "embed_v1",
) -> EmbeddingEngine:
    """
    Get the global embedding engine instance.

    Args:
        model: Embedding model
        ollama_host: Ollama host
        dimension: Embedding dimension
        version: Embedding version

    Returns:
        EmbeddingEngine: Singleton instance
    """
    global _embedding_engine
    if _embedding_engine is None:
        _embedding_engine = EmbeddingEngine(
            model=model,
            ollama_host=ollama_host,
            dimension=dimension,
            version=version,
        )
    return _embedding_engine


async def close_embedding_engine() -> None:
    """Close the global embedding engine."""
    global _embedding_engine
    if _embedding_engine is not None:
        await _embedding_engine.close()
        _embedding_engine = None
