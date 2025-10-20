"""
Unit tests for Vault cryptography.

Tests key derivation and encryption/decryption with mocked dependencies.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from neura.vault.crypto import VaultCrypto


class TestVaultCrypto:
    """Test VaultCrypto class."""

    def test_initialization(self) -> None:
        """Test crypto initialization with parameters."""
        crypto = VaultCrypto(
            memory_cost=32768,  # 32 MB
            time_cost=2,
            parallelism=2,
        )

        assert crypto.memory_cost == 32768
        assert crypto.time_cost == 2
        assert crypto.parallelism == 2

    def test_generate_salt(self) -> None:
        """Test salt generation."""
        crypto = VaultCrypto()

        salt = crypto.generate_salt()

        assert len(salt) == 32
        assert isinstance(salt, bytes)

        # Generate another - should be different
        salt2 = crypto.generate_salt()
        assert salt != salt2

    @patch("neura.vault.crypto.hash_secret_raw")
    def test_derive_key(self, mock_hash: MagicMock) -> None:
        """Test key derivation."""
        crypto = VaultCrypto()

        # Mock Argon2 hash
        expected_key = os.urandom(32)
        mock_hash.return_value = expected_key

        password = "test_password"
        salt = crypto.generate_salt()

        key = crypto.derive_key(password, salt)

        assert key == expected_key
        assert len(key) == 32

        # Verify hash_secret_raw was called correctly
        mock_hash.assert_called_once()
        call_kwargs = mock_hash.call_args.kwargs
        assert call_kwargs["hash_len"] == 32

    def test_encrypt_decrypt(self) -> None:
        """Test encryption and decryption."""
        crypto = VaultCrypto()

        # Generate a key
        key = os.urandom(32)
        plaintext = b"This is a secret message"

        # Encrypt
        result = crypto.encrypt(plaintext, key)
        assert result.is_success()

        nonce, ciphertext = result.data

        assert len(nonce) == 12  # GCM nonce
        assert ciphertext != plaintext
        assert len(ciphertext) > len(plaintext)  # Includes auth tag

        # Decrypt
        result = crypto.decrypt(nonce, ciphertext, key)
        assert result.is_success()

        decrypted = result.data
        assert decrypted == plaintext

    def test_decrypt_with_wrong_key(self) -> None:
        """Test decryption with wrong key fails."""
        crypto = VaultCrypto()

        key1 = os.urandom(32)
        key2 = os.urandom(32)
        plaintext = b"Secret"

        # Encrypt with key1
        result = crypto.encrypt(plaintext, key1)
        nonce, ciphertext = result.data

        # Try to decrypt with key2
        result = crypto.decrypt(nonce, ciphertext, key2)
        assert result.is_failure()
        assert "decrypt" in result.error.lower()

    def test_decrypt_with_tampered_data(self) -> None:
        """Test decryption with tampered ciphertext fails."""
        crypto = VaultCrypto()

        key = os.urandom(32)
        plaintext = b"Secret"

        # Encrypt
        result = crypto.encrypt(plaintext, key)
        nonce, ciphertext = result.data

        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 1  # Flip one bit
        tampered_bytes = bytes(tampered)

        # Try to decrypt
        result = crypto.decrypt(nonce, tampered_bytes, key)
        assert result.is_failure()

    def test_encrypt_file(self, tmp_path) -> None:
        """Test file encryption."""
        crypto = VaultCrypto()

        # Create test file
        input_file = tmp_path / "plaintext.txt"
        input_file.write_bytes(b"Secret file content")

        output_file = tmp_path / "encrypted.bin"
        key = os.urandom(32)

        # Encrypt
        result = crypto.encrypt_file(str(input_file), str(output_file), key)
        assert result.is_success()
        assert output_file.exists()

        # Encrypted file should be different
        encrypted_content = output_file.read_bytes()
        assert encrypted_content != b"Secret file content"

    def test_decrypt_file(self, tmp_path) -> None:
        """Test file decryption."""
        crypto = VaultCrypto()

        # Create and encrypt file
        input_file = tmp_path / "plaintext.txt"
        original_content = b"Secret file content"
        input_file.write_bytes(original_content)

        encrypted_file = tmp_path / "encrypted.bin"
        key = os.urandom(32)

        crypto.encrypt_file(str(input_file), str(encrypted_file), key)

        # Decrypt
        decrypted_file = tmp_path / "decrypted.txt"
        result = crypto.decrypt_file(str(encrypted_file), str(decrypted_file), key)

        assert result.is_success()
        assert decrypted_file.exists()

        # Content should match original
        decrypted_content = decrypted_file.read_bytes()
        assert decrypted_content == original_content

    def test_secure_erase(self) -> None:
        """Test secure erase of sensitive data."""
        crypto = VaultCrypto()

        # Create sensitive data
        data = bytearray(b"sensitive_key_12345678901234567890")

        # Erase
        crypto.secure_erase(data)

        # Note: In Python, we can't truly verify erasure due to GC
        # This test just ensures the method doesn't crash


class TestVaultCryptoIntegration:
    """Integration tests for crypto operations."""

    def test_full_encryption_flow(self) -> None:
        """Test complete encryption workflow."""
        crypto = VaultCrypto(
            memory_cost=16384,  # Smaller for tests
            time_cost=1,
            parallelism=1,
        )

        # Simulate user password
        password = "MySecurePassword123!"
        salt = crypto.generate_salt()

        # Derive key
        key = crypto.derive_key(password, salt)
        assert len(key) == 32

        # Encrypt multiple pieces of data
        data1 = b"API Key: abc123"
        data2 = b"Database Password: xyz789"

        result1 = crypto.encrypt(data1, key)
        result2 = crypto.encrypt(data2, key)

        assert result1.is_success()
        assert result2.is_success()

        nonce1, ciphertext1 = result1.data
        nonce2, ciphertext2 = result2.data

        # Decrypt
        decrypt1 = crypto.decrypt(nonce1, ciphertext1, key)
        decrypt2 = crypto.decrypt(nonce2, ciphertext2, key)

        assert decrypt1.is_success()
        assert decrypt2.is_success()
        assert decrypt1.data == data1
        assert decrypt2.data == data2

    def test_different_passwords_different_keys(self) -> None:
        """Test that different passwords produce different keys."""
        crypto = VaultCrypto()

        salt = crypto.generate_salt()

        key1 = crypto.derive_key("password1", salt)
        key2 = crypto.derive_key("password2", salt)

        assert key1 != key2

    def test_same_password_same_salt_same_key(self) -> None:
        """Test that same password and salt produce same key."""
        crypto = VaultCrypto()

        salt = crypto.generate_salt()
        password = "test_password"

        key1 = crypto.derive_key(password, salt)
        key2 = crypto.derive_key(password, salt)

        assert key1 == key2
