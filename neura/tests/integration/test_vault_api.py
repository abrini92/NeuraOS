"""
Integration tests for Vault API endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app
from neura.vault.types import VaultState, VaultStatus


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestVaultEndpoints:
    """Test Vault API endpoints."""

    @patch("neura.vault.router.get_vault_manager")
    def test_vault_info(self, mock_get_manager, client: TestClient) -> None:
        """Test /api/vault/ endpoint."""
        response = client.get("/api/vault/")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "vault"
        assert data["status"] == "operational"
        assert "endpoints" in data

    @patch("neura.vault.router.get_vault_manager")
    def test_unlock_vault_success(self, mock_get_manager, client: TestClient) -> None:
        """Test successful vault unlock."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.unlock.return_value = Result.success(True)
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/api/vault/unlock",
            json={"password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "unlocked" in data["message"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_unlock_vault_invalid_password(
        self, mock_get_manager, client: TestClient
    ) -> None:
        """Test unlock with invalid password."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.unlock.return_value = Result.failure("Invalid password")
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/api/vault/unlock",
            json={"password": "wrong_password"},
        )

        assert response.status_code == 401
        assert "Invalid password" in response.json()["detail"]

    @patch("neura.vault.router.get_vault_manager")
    def test_lock_vault(self, mock_get_manager, client: TestClient) -> None:
        """Test locking vault."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.lock.return_value = Result.success(True)
        mock_get_manager.return_value = mock_manager

        response = client.post("/api/vault/lock")

        assert response.status_code == 200
        data = response.json()
        assert "locked" in data["message"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_panic_vault(self, mock_get_manager, client: TestClient) -> None:
        """Test panic mode."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.panic.return_value = Result.success(True)
        mock_get_manager.return_value = mock_manager

        response = client.post("/api/vault/panic")

        assert response.status_code == 200
        data = response.json()
        assert "panic" in data["message"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_put_secret_success(self, mock_get_manager, client: TestClient) -> None:
        """Test storing a secret."""
        from neura.core.types import Result
        from neura.vault.types import SecretEntry, SecretMetadata

        mock_manager = AsyncMock()
        mock_manager.is_unlocked.return_value = True
        
        mock_entry = SecretEntry(
            name="api_key",
            value="secret_value",
            metadata=SecretMetadata(),
        )
        mock_manager.put_secret.return_value = Result.success(mock_entry)
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/api/vault/put",
            json={
                "name": "api_key",
                "value": "secret_value",
                "metadata": {"description": "My API key"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "stored" in data["message"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_put_secret_vault_locked(
        self, mock_get_manager, client: TestClient
    ) -> None:
        """Test storing secret when vault is locked."""
        from unittest.mock import MagicMock
        
        mock_manager = MagicMock()
        mock_manager.is_unlocked.return_value = False
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/api/vault/put",
            json={"name": "key", "value": "value"},
        )

        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_get_secret_success(self, mock_get_manager, client: TestClient) -> None:
        """Test retrieving a secret."""
        from neura.core.types import Result
        from neura.vault.types import SecretEntry, SecretMetadata

        mock_manager = AsyncMock()
        mock_manager.is_unlocked.return_value = True

        mock_entry = SecretEntry(
            name="api_key",
            value="secret_value",
            metadata=SecretMetadata(),
        )
        mock_manager.get_secret.return_value = Result.success(mock_entry)
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/vault/get?name=api_key")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "api_key"
        assert data["value"] == "secret_value"

    @patch("neura.vault.router.get_vault_manager")
    def test_get_secret_not_found(self, mock_get_manager, client: TestClient) -> None:
        """Test getting non-existent secret."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.is_unlocked.return_value = True
        mock_manager.get_secret.return_value = Result.failure("Secret not found")
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/vault/get?name=nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_list_secrets(self, mock_get_manager, client: TestClient) -> None:
        """Test listing secrets."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.is_unlocked.return_value = True
        mock_manager.list_secrets.return_value = Result.success(
            ["key1", "key2", "key3"]
        )
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/vault/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "key1" in data

    @patch("neura.vault.router.get_vault_manager")
    def test_delete_secret(self, mock_get_manager, client: TestClient) -> None:
        """Test deleting a secret."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.is_unlocked.return_value = True
        mock_manager.delete_secret.return_value = Result.success(True)
        mock_get_manager.return_value = mock_manager

        response = client.delete("/api/vault/delete?name=api_key")

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_get_status(self, mock_get_manager, client: TestClient) -> None:
        """Test getting vault status."""
        from unittest.mock import MagicMock
        
        mock_manager = MagicMock()
        mock_status = VaultStatus(
            state=VaultState.LOCKED,
            total_secrets=5,
            auto_lock_enabled=True,
            idle_timeout_seconds=300,
        )
        mock_manager.get_status.return_value = mock_status
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/vault/status")

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "locked"
        assert data["total_secrets"] == 5


class TestVaultSecurity:
    """Test security aspects of Vault API."""

    @patch("neura.vault.router.get_vault_manager")
    def test_operations_require_unlock(
        self, mock_get_manager, client: TestClient
    ) -> None:
        """Test that operations require unlocked vault."""
        from unittest.mock import MagicMock
        
        mock_manager = MagicMock()
        mock_manager.is_unlocked.return_value = False
        mock_get_manager.return_value = mock_manager

        # Try various operations
        operations = [
            ("POST", "/api/vault/put", {"name": "k", "value": "v"}),
            ("GET", "/api/vault/get?name=k", None),
            ("GET", "/api/vault/list", None),
            ("DELETE", "/api/vault/delete?name=k", None),
        ]

        for method, url, json_data in operations:
            if method == "POST":
                response = client.post(url, json=json_data)
            elif method == "GET":
                response = client.get(url)
            elif method == "DELETE":
                response = client.delete(url)

            assert response.status_code == 403
            assert "locked" in response.json()["detail"].lower()

    @patch("neura.vault.router.get_vault_manager")
    def test_password_not_logged(self, mock_get_manager, client: TestClient, caplog) -> None:
        """Test that passwords are not logged."""
        from neura.core.types import Result

        mock_manager = AsyncMock()
        mock_manager.unlock.return_value = Result.success(True)
        mock_get_manager.return_value = mock_manager

        password = "super_secret_password_123"

        response = client.post(
            "/api/vault/unlock",
            json={"password": password},
        )

        # Check that password is not in logs
        for record in caplog.records:
            assert password not in record.message
