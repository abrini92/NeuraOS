"""
Cryptographic functions for Vault.

Provides key derivation (Argon2id) and file encryption/decryption.
"""

import logging
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from neura.core.types import Result

logger = logging.getLogger(__name__)


class VaultCrypto:
    """
    Cryptographic operations for Vault.

    Uses Argon2id for key derivation and AES-256-GCM for encryption.

    Example:
        >>> crypto = VaultCrypto()
        >>> key = crypto.derive_key("my_password", salt)
        >>> encrypted = crypto.encrypt(b"secret data", key)
    """

    def __init__(
        self,
        memory_cost: int = 65536,  # 64 MB in KB
        time_cost: int = 3,
        parallelism: int = 4,
    ) -> None:
        """
        Initialize crypto with Argon2id parameters.

        Args:
            memory_cost: Memory cost in KB (default: 64MB)
            time_cost: Number of iterations (default: 3)
            parallelism: Degree of parallelism (default: 4)
        """
        self.memory_cost = memory_cost
        self.time_cost = time_cost
        self.parallelism = parallelism

        logger.info(
            f"VaultCrypto initialized: mem={memory_cost}KB, "
            f"time={time_cost}, parallel={parallelism}"
        )

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive a 256-bit key from password using Argon2id.

        Args:
            password: Master password
            salt: Random salt (32 bytes recommended)

        Returns:
            bytes: 32-byte derived key

        Example:
            >>> salt = os.urandom(32)
            >>> key = crypto.derive_key("password", salt)
            >>> len(key)
            32
        """
        try:
            key = hash_secret_raw(
                secret=password.encode("utf-8"),
                salt=salt,
                time_cost=self.time_cost,
                memory_cost=self.memory_cost,
                parallelism=self.parallelism,
                hash_len=32,  # 256 bits
                type=Type.ID,  # Argon2id
            )

            logger.debug("Key derived successfully")
            return key

        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise

    def generate_salt(self) -> bytes:
        """
        Generate a random salt for key derivation.

        Returns:
            bytes: 32-byte random salt
        """
        return os.urandom(32)

    def encrypt(self, plaintext: bytes, key: bytes) -> Result[tuple[bytes, bytes]]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key

        Returns:
            Result[Tuple[bytes, bytes]]: (nonce, ciphertext) or error

        Example:
            >>> result = crypto.encrypt(b"secret", key)
            >>> if result.is_success():
            ...     nonce, ciphertext = result.data
        """
        try:
            # Generate random nonce
            nonce = os.urandom(12)  # 96 bits for GCM

            # Create cipher
            aesgcm = AESGCM(key)

            # Encrypt (includes authentication tag)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            logger.debug(f"Encrypted {len(plaintext)} bytes")
            return Result.success((nonce, ciphertext))

        except Exception as e:
            error_msg = f"Encryption failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def decrypt(self, nonce: bytes, ciphertext: bytes, key: bytes) -> Result[bytes]:
        """
        Decrypt data using AES-256-GCM.

        Args:
            nonce: 12-byte nonce used for encryption
            ciphertext: Encrypted data (includes auth tag)
            key: 32-byte encryption key

        Returns:
            Result[bytes]: Decrypted plaintext or error

        Example:
            >>> result = crypto.decrypt(nonce, ciphertext, key)
            >>> if result.is_success():
            ...     plaintext = result.data
        """
        try:
            # Create cipher
            aesgcm = AESGCM(key)

            # Decrypt and verify authentication tag
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            logger.debug(f"Decrypted {len(plaintext)} bytes")
            return Result.success(plaintext)

        except Exception as e:
            error_msg = f"Decryption failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def encrypt_file(self, input_path: str, output_path: str, key: bytes) -> Result[bool]:
        """
        Encrypt a file.

        Args:
            input_path: Path to plaintext file
            output_path: Path to write encrypted file
            key: 32-byte encryption key

        Returns:
            Result[bool]: Success or error
        """
        try:
            # Read plaintext
            with open(input_path, "rb") as f:
                plaintext = f.read()

            # Encrypt
            result = self.encrypt(plaintext, key)
            if result.is_failure():
                return Result.failure(result.error)

            nonce, ciphertext = result.data

            # Write encrypted (nonce + ciphertext)
            with open(output_path, "wb") as f:
                f.write(nonce)
                f.write(ciphertext)

            logger.info(f"File encrypted: {input_path} -> {output_path}")
            return Result.success(True)

        except Exception as e:
            error_msg = f"File encryption failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def decrypt_file(self, input_path: str, output_path: str, key: bytes) -> Result[bool]:
        """
        Decrypt a file.

        Args:
            input_path: Path to encrypted file
            output_path: Path to write decrypted file
            key: 32-byte encryption key

        Returns:
            Result[bool]: Success or error
        """
        try:
            # Read encrypted
            with open(input_path, "rb") as f:
                nonce = f.read(12)
                ciphertext = f.read()

            # Decrypt
            result = self.decrypt(nonce, ciphertext, key)
            if result.is_failure():
                return Result.failure(result.error)

            plaintext = result.data

            # Write decrypted
            with open(output_path, "wb") as f:
                f.write(plaintext)

            logger.info(f"File decrypted: {input_path} -> {output_path}")
            return Result.success(True)

        except Exception as e:
            error_msg = f"File decryption failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def secure_erase(self, data: bytes) -> None:
        """
        Securely erase sensitive data from memory.

        Args:
            data: Bytes to erase
        """
        # Overwrite with zeros (best effort in Python)
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
        # Note: In Python, true secure erasure is difficult due to GC
        # This is a best-effort approach
        logger.debug("Secure erase performed")


# Singleton instance
_vault_crypto: VaultCrypto | None = None


def get_vault_crypto(
    memory_cost: int = 65536,
    time_cost: int = 3,
    parallelism: int = 4,
) -> VaultCrypto:
    """
    Get the global VaultCrypto instance.

    Args:
        memory_cost: Argon2 memory cost in KB
        time_cost: Argon2 time cost
        parallelism: Argon2 parallelism

    Returns:
        VaultCrypto: Singleton instance
    """
    global _vault_crypto
    if _vault_crypto is None:
        _vault_crypto = VaultCrypto(
            memory_cost=memory_cost,
            time_cost=time_cost,
            parallelism=parallelism,
        )
    return _vault_crypto
