"""
Vault types and data models.

Defines Pydantic models for vault operations and secrets.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, SecretStr


class VaultState(str, Enum):
    """Vault lock state."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"
    PANIC = "panic"


class SecretMetadata(BaseModel):
    """Metadata for a secret."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: datetime | None = None
    access_count: int = Field(default=0)
    tags: list[str] = Field(default_factory=list)
    description: str | None = None


class SecretEntry(BaseModel):
    """A secret stored in the vault."""

    name: str = Field(..., description="Secret name (unique identifier)")
    value: SecretStr = Field(..., description="Secret value (encrypted)")
    metadata: SecretMetadata = Field(default_factory=SecretMetadata)


class VaultStatus(BaseModel):
    """Vault status information."""

    state: VaultState = Field(..., description="Current vault state")
    total_secrets: int = Field(default=0, description="Number of secrets stored")
    last_unlock: datetime | None = Field(None, description="Last unlock timestamp")
    last_lock: datetime | None = Field(None, description="Last lock timestamp")
    auto_lock_enabled: bool = Field(default=True, description="Auto-lock enabled")
    idle_timeout_seconds: int = Field(default=300, description="Idle timeout in seconds")


class UnlockRequest(BaseModel):
    """Request to unlock the vault."""

    password: SecretStr = Field(..., min_length=8, description="Master password")


class PutSecretRequest(BaseModel):
    """Request to store a secret."""

    name: str = Field(..., min_length=1, description="Secret name")
    value: SecretStr = Field(..., min_length=1, description="Secret value")
    metadata: dict[str, Any] | None = Field(None, description="Optional metadata")


class GetSecretResponse(BaseModel):
    """Response for getting a secret."""

    name: str
    value: str  # Decrypted value (only returned when vault unlocked)
    metadata: SecretMetadata


class VaultConfig(BaseModel):
    """Configuration for Vault module."""

    db_path: str = Field(default="neura_vault/secrets.db", description="SQLCipher database path")
    idle_timeout: int = Field(default=300, ge=60, description="Auto-lock timeout in seconds")
    argon2_memory: int = Field(default=65536, description="Argon2 memory cost in KB (64MB)")
    argon2_iterations: int = Field(default=3, description="Argon2 time cost")
    argon2_parallelism: int = Field(default=4, description="Argon2 parallelism")
    sqlcipher_page_size: int = Field(default=4096, description="SQLCipher page size")
    sqlcipher_kdf_iter: int = Field(default=256000, description="SQLCipher KDF iterations")
