"""
Configuration management for Neura.

Loads configuration from environment variables and provides
a singleton Config instance.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class NeuraSettings(BaseSettings):
    """
    Neura configuration settings.

    Settings are loaded from environment variables with NEURA_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="NEURA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    api_workers: int = 1

    # Paths
    data_dir: Path = Path("./data")
    logs_dir: Path = Path("./logs")
    vault_dir: Path = Path("./neura_vault")

    # Logging
    log_level: str = "INFO"
    debug: bool = False

    # Cortex (LLM)
    cortex_model: str = "llama3"
    cortex_temperature: float = 0.7
    cortex_max_tokens: int = 2048

    # Memory
    memory_db_path: Path = Path("./data/memory.db")
    memory_vector_size: int = 768
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    embedding_model: str = "mxbai-embed-large"
    embedding_version: str = "embed_v1"
    context_window_size: int = 4096
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Vault
    vault_key_iterations: int = 100_000
    vault_salt_length: int = 32

    def __init__(self, **kwargs):  # type: ignore
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)


# Singleton instance
_settings: NeuraSettings | None = None


def get_settings() -> NeuraSettings:
    """
    Get the global settings instance.

    Returns:
        NeuraSettings: The singleton settings instance
    """
    global _settings
    if _settings is None:
        _settings = NeuraSettings()
    return _settings


def reload_settings() -> NeuraSettings:
    """
    Reload settings from environment.

    Useful for testing or when configuration changes.

    Returns:
        NeuraSettings: The new settings instance
    """
    global _settings
    _settings = NeuraSettings()
    return _settings
