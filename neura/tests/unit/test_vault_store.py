"""
Unit tests for Vault store.

Tests encrypted storage with mocked SQL Cipher.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from neura.vault.store import VaultStore
from neura.vault.types import SecretEntry


class TestVaultStore:
    """Test VaultStore class."""

    @pytest.fixture
    def test_key(self) -> bytes:
        """Generate a test encryption key."""
        return os.urandom(32)

    @pytest.fixture
    def vault_store(self, tmp_path) -> VaultStore:
        """Create a test vault store."""
        db_path = str(tmp_path / "test_vault.db")
        return VaultStore(db_path=db_path)

    @patch("neura.vault.store.sqlite3.connect")
    def test_open_success(
        self, mock_connect: MagicMock, vault_store: VaultStore, test_key: bytes
    ) -> None:
        """Test opening vault with correct key."""
        # Mock connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Mock cursor for PRAGMA and SELECT queries
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)  # Return tuple for SELECT 1
        mock_conn.execute.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor

        result = vault_store.open(test_key)

        assert result.is_success()
        assert vault_store.is_open()

        # Verify execute was called (connection established)
        assert mock_conn.execute.called

    @patch("neura.vault.store.sqlite3.connect")
    def test_open_invalid_key(
        self, mock_connect: MagicMock, vault_store: VaultStore, test_key: bytes
    ) -> None:
        """Test opening vault with invalid key fails."""
        # Mock connection that raises on query
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        import sqlite3
        mock_conn.execute.side_effect = sqlite3.DatabaseError("file is not a database")

        result = vault_store.open(test_key)

        assert result.is_failure()
        assert ("invalid" in result.error.lower() or "database" in result.error.lower())
        assert not vault_store.is_open()

    @patch("neura.vault.store.sqlite3.connect")
    def test_put_secret_new(
        self, mock_connect: MagicMock, vault_store: VaultStore, test_key: bytes
    ) -> None:
        """Test storing a new secret."""
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True
        
        # Initialize encryption
        from neura.vault.crypto import VaultCrypto
        vault_store._crypto = VaultCrypto(test_key)
        vault_store._encryption_key = test_key

        # Encrypt the test value to get proper encrypted format
        from neura.vault.crypto import VaultCrypto
        crypto = VaultCrypto(test_key)
        encrypt_result = crypto.encrypt(b"secret_value", test_key)
        nonce, ciphertext = encrypt_result.data
        value_encrypted = nonce + ciphertext

        # Mock fetchone to return None (secret doesn't exist), then return the stored secret
        mock_row = {
            "name": "api_key",
            "value_encrypted": value_encrypted,
            "metadata": "{}",
            "created_at": "2025-10-18T00:00:00",
            "updated_at": "2025-10-18T00:00:00",
            "accessed_at": None,
            "access_count": 0,
        }
        mock_conn.execute.return_value.fetchone.side_effect = [None, mock_row]

        result = vault_store.put_secret("api_key", "secret_value")

        assert result.is_success()
        entry = result.data
        assert entry.name == "api_key"

    @patch("neura.vault.store.sqlite3.connect")
    def test_put_secret_locked_vault(
        self, mock_connect: MagicMock, vault_store: VaultStore
    ) -> None:
        """Test putting secret fails when vault is locked."""
        vault_store._is_open = False

        result = vault_store.put_secret("key", "value")

        assert result.is_failure()
        assert "not open" in result.error.lower()

    @patch("neura.vault.store.sqlite3.connect")
    def test_get_secret_success(
        self, mock_connect: MagicMock, vault_store: VaultStore, test_key: bytes
    ) -> None:
        """Test retrieving a secret."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True
        
        # Initialize encryption
        from neura.vault.crypto import VaultCrypto
        vault_store._crypto = VaultCrypto(test_key)
        vault_store._encryption_key = test_key

        # Encrypt the test value
        crypto = VaultCrypto(test_key)
        encrypt_result = crypto.encrypt(b"secret_value", test_key)
        nonce, ciphertext = encrypt_result.data
        value_encrypted = nonce + ciphertext

        # Mock secret exists
        mock_row = {
            "name": "api_key",
            "value_encrypted": value_encrypted,
            "metadata": '{"description": "Test key"}',
            "created_at": "2025-10-18T00:00:00",
            "updated_at": "2025-10-18T00:00:00",
            "accessed_at": None,
            "access_count": 0,
        }
        mock_conn.execute.return_value.fetchone.return_value = mock_row

        result = vault_store.get_secret("api_key")

        assert result.is_success()
        entry = result.data
        assert entry.name == "api_key"
        assert entry.value.get_secret_value() == "secret_value"

    @patch("neura.vault.store.sqlite3.connect")
    def test_get_secret_not_found(
        self, mock_connect: MagicMock, vault_store: VaultStore, test_key: bytes
    ) -> None:
        """Test getting non-existent secret."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True
        
        # Initialize encryption
        from neura.vault.crypto import VaultCrypto
        vault_store._crypto = VaultCrypto(test_key)
        vault_store._encryption_key = test_key

        # Mock secret doesn't exist
        mock_conn.execute.return_value.fetchone.return_value = None

        result = vault_store.get_secret("nonexistent")

        assert result.is_failure()
        assert "not found" in result.error.lower()

    @patch("neura.vault.store.sqlite3.connect")
    def test_list_secrets(
        self, mock_connect: MagicMock, vault_store: VaultStore
    ) -> None:
        """Test listing all secrets."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True

        # Mock secrets
        mock_rows = [{"name": "key1"}, {"name": "key2"}, {"name": "key3"}]
        mock_conn.execute.return_value.fetchall.return_value = mock_rows

        result = vault_store.list_secrets()

        assert result.is_success()
        names = result.data
        assert len(names) == 3
        assert "key1" in names
        assert "key2" in names
        assert "key3" in names

    @patch("neura.vault.store.sqlite3.connect")
    def test_delete_secret(
        self, mock_connect: MagicMock, vault_store: VaultStore
    ) -> None:
        """Test deleting a secret."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True

        # Mock successful delete
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.execute.return_value = mock_cursor

        result = vault_store.delete_secret("api_key")

        assert result.is_success()

    @patch("neura.vault.store.sqlite3.connect")
    def test_delete_secret_not_found(
        self, mock_connect: MagicMock, vault_store: VaultStore
    ) -> None:
        """Test deleting non-existent secret."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True

        # Mock no rows affected
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor

        result = vault_store.delete_secret("nonexistent")

        assert result.is_failure()
        assert "not found" in result.error.lower()

    def test_close(self, vault_store: VaultStore) -> None:
        """Test closing vault store."""
        mock_conn = MagicMock()
        vault_store._conn = mock_conn
        vault_store._is_open = True

        vault_store.close()

        assert not vault_store.is_open()
        mock_conn.close.assert_called_once()

    @patch("neura.vault.store.sqlite3.connect")
    def test_count_secrets(
        self, mock_connect: MagicMock, vault_store: VaultStore
    ) -> None:
        """Test counting secrets."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        vault_store._conn = mock_conn
        vault_store._is_open = True

        # Mock count
        mock_conn.execute.return_value.fetchone.return_value = {"count": 5}

        count = vault_store.count_secrets()
        assert count == 5
