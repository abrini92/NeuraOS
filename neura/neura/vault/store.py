"""
Encrypted storage using SQLite + application-level encryption.

Provides secure storage for secrets with AES-256-GCM encryption.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from neura.core.types import Result
from neura.vault.crypto import VaultCrypto
from neura.vault.types import SecretEntry, SecretMetadata

logger = logging.getLogger(__name__)


class VaultStore:
    """
    Encrypted storage for secrets using SQLite + AES-256-GCM.

    Values are encrypted at application level before storage.
    Metadata (key names, timestamps) stored in plaintext for indexing.

    Example:
        >>> store = VaultStore(db_path="secrets.db")
        >>> store.open(encryption_key)
        >>> result = store.put_secret("api_key", "secret_value")
    """

    def __init__(
        self,
        db_path: str = "neura_vault/secrets.db",
    ) -> None:
        """
        Initialize vault store.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._crypto: VaultCrypto | None = None
        self._encryption_key: bytes | None = None
        self._is_open = False

        logger.info(f"VaultStore created: {db_path}")

    def open(self, key: bytes) -> Result[bool]:
        """
        Open the database and initialize encryption.

        Args:
            key: 32-byte encryption key for AES-256-GCM

        Returns:
            Result[bool]: Success or error
        """
        try:
            # Validate key length
            if len(key) != 32:
                return Result.failure(f"Invalid key length: {len(key)} (expected 32 bytes)")

            # Create directory if needed
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect to SQLite database (standard, not SQLCipher)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row

            # Store encryption key and initialize crypto
            self._encryption_key = key
            self._crypto = VaultCrypto()

            # Create tables if needed
            self._create_tables()

            self._is_open = True
            logger.info("VaultStore opened successfully (application-level encryption)")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Failed to open vault: {e}"
            logger.error(error_msg)
            if self._conn:
                self._conn.close()
                self._conn = None
            self._encryption_key = None
            self._crypto = None
            return Result.failure(error_msg)

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self._conn:
            return

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secrets (
                name TEXT PRIMARY KEY,
                value_encrypted BLOB NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                accessed_at TEXT,
                access_count INTEGER DEFAULT 0
            )
        """
        )

        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secrets_created
            ON secrets(created_at)
        """
        )

        self._conn.commit()
        logger.debug("Database tables created (with encrypted values)")

    def close(self) -> None:
        """Close the database connection and clear encryption key from memory."""
        if self._conn:
            self._conn.close()
            self._conn = None

        # Securely erase encryption key from memory
        if self._encryption_key is not None:
            # Overwrite with zeros before deletion
            self._encryption_key = b"\x00" * len(self._encryption_key)
            del self._encryption_key
            self._encryption_key = None

        self._crypto = None
        self._is_open = False
        logger.info("VaultStore closed (encryption key erased)")

    def is_open(self) -> bool:
        """Check if the store is open."""
        return self._is_open

    def put_secret(
        self,
        name: str,
        value: str,
        metadata: dict | None = None,
    ) -> Result[SecretEntry]:
        """
        Store a secret (value is encrypted before storage).

        Args:
            name: Secret name (unique)
            value: Secret value (will be encrypted)
            metadata: Optional metadata

        Returns:
            Result[SecretEntry]: Stored secret or error
        """
        if not self._is_open or not self._conn:
            return Result.failure("Vault is not open")

        if not self._crypto or not self._encryption_key:
            return Result.failure("Encryption not initialized")

        try:
            now = datetime.utcnow().isoformat()

            # Encrypt the value
            plaintext = value.encode("utf-8")
            encrypt_result = self._crypto.encrypt(plaintext, self._encryption_key)

            if encrypt_result.is_failure():
                return Result.failure(f"Encryption failed: {encrypt_result.error}")

            nonce, ciphertext = encrypt_result.data
            # Store as: nonce (12 bytes) + ciphertext
            value_encrypted = nonce + ciphertext

            # Check if exists
            existing = self._conn.execute(
                "SELECT * FROM secrets WHERE name = ?", (name,)
            ).fetchone()

            if existing:
                # Update existing
                self._conn.execute(
                    """
                    UPDATE secrets
                    SET value_encrypted = ?, metadata = ?, updated_at = ?
                    WHERE name = ?
                    """,
                    (value_encrypted, json.dumps(metadata or {}), now, name),
                )
                logger.info(f"Secret updated (encrypted): {name}")
            else:
                # Insert new
                self._conn.execute(
                    """
                    INSERT INTO secrets (name, value_encrypted, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, value_encrypted, json.dumps(metadata or {}), now, now),
                )
                logger.info(f"Secret created (encrypted): {name}")

            self._conn.commit()

            # Retrieve and return
            return self.get_secret(name)

        except Exception as e:
            error_msg = f"Failed to store secret: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def get_secret(self, name: str) -> Result[SecretEntry]:
        """
        Get a secret by name (value is decrypted on retrieval).

        Args:
            name: Secret name

        Returns:
            Result[SecretEntry]: Secret with decrypted value or error
        """
        if not self._is_open or not self._conn:
            return Result.failure("Vault is not open")

        if not self._crypto or not self._encryption_key:
            return Result.failure("Encryption not initialized")

        try:
            row = self._conn.execute("SELECT * FROM secrets WHERE name = ?", (name,)).fetchone()

            if not row:
                return Result.failure(f"Secret not found: {name}")

            # Decrypt the value
            value_encrypted = row["value_encrypted"]

            # Extract nonce (first 12 bytes) and ciphertext (rest)
            nonce = value_encrypted[:12]
            ciphertext = value_encrypted[12:]

            decrypt_result = self._crypto.decrypt(nonce, ciphertext, self._encryption_key)

            if decrypt_result.is_failure():
                return Result.failure(f"Decryption failed: {decrypt_result.error}")

            value_plaintext = decrypt_result.data.decode("utf-8")

            # Update access stats
            now = datetime.utcnow().isoformat()
            self._conn.execute(
                """
                UPDATE secrets
                SET accessed_at = ?, access_count = access_count + 1
                WHERE name = ?
                """,
                (now, name),
            )
            self._conn.commit()

            # Parse metadata
            metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
            metadata = SecretMetadata(
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                accessed_at=datetime.fromisoformat(row["accessed_at"])
                if row["accessed_at"]
                else None,
                access_count=row["access_count"] + 1,  # Include current access
                **metadata_dict,
            )

            entry = SecretEntry(
                name=row["name"],
                value=value_plaintext,  # Decrypted value
                metadata=metadata,
            )

            logger.debug(f"Secret retrieved (decrypted): {name}")
            return Result.success(entry)

        except Exception as e:
            error_msg = f"Failed to get secret: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def list_secrets(self) -> Result[list[str]]:
        """
        List all secret names.

        Returns:
            Result[List[str]]: List of secret names or error
        """
        if not self._is_open or not self._conn:
            return Result.failure("Vault is not open")

        try:
            cursor = self._conn.execute("SELECT name FROM secrets ORDER BY name")
            names = [row["name"] for row in cursor.fetchall()]

            logger.debug(f"Listed {len(names)} secrets")
            return Result.success(names)

        except Exception as e:
            error_msg = f"Failed to list secrets: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def delete_secret(self, name: str) -> Result[bool]:
        """
        Delete a secret.

        Args:
            name: Secret name

        Returns:
            Result[bool]: Success or error
        """
        if not self._is_open or not self._conn:
            return Result.failure("Vault is not open")

        try:
            cursor = self._conn.execute("DELETE FROM secrets WHERE name = ?", (name,))

            if cursor.rowcount == 0:
                return Result.failure(f"Secret not found: {name}")

            self._conn.commit()
            logger.info(f"Secret deleted: {name}")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Failed to delete secret: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def count_secrets(self) -> int:
        """Count total secrets."""
        if not self._is_open or not self._conn:
            return 0

        try:
            cursor = self._conn.execute("SELECT COUNT(*) as count FROM secrets")
            return cursor.fetchone()["count"]
        except Exception:
            return 0


# Singleton instance
_vault_store: VaultStore | None = None


def get_vault_store(
    db_path: str = "neura_vault/secrets.db",
    page_size: int = 4096,
    kdf_iter: int = 256000,
) -> VaultStore:
    """
    Get the global VaultStore instance.

    Args:
        db_path: Database path
        page_size: SQLCipher page size
        kdf_iter: SQLCipher KDF iterations

    Returns:
        VaultStore: Singleton instance
    """
    global _vault_store
    if _vault_store is None:
        _vault_store = VaultStore(
            db_path=db_path,
        )
    return _vault_store
