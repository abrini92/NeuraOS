"""
Vault module - Encrypted secrets management.

The Vault module provides:
- SQLCipher encrypted storage
- Argon2id key derivation
- Auto-lock and panic mode
- WHY Journal logging
"""

from neura.vault.crypto import VaultCrypto, get_vault_crypto
from neura.vault.manager import VaultManager, get_vault_manager
from neura.vault.router import router
from neura.vault.store import VaultStore, get_vault_store
from neura.vault.types import (
    GetSecretResponse,
    PutSecretRequest,
    SecretEntry,
    UnlockRequest,
    VaultState,
    VaultStatus,
)

__all__ = [
    "VaultCrypto",
    "get_vault_crypto",
    "VaultStore",
    "get_vault_store",
    "VaultManager",
    "get_vault_manager",
    "router",
    "SecretEntry",
    "VaultState",
    "VaultStatus",
    "UnlockRequest",
    "PutSecretRequest",
    "GetSecretResponse",
]
