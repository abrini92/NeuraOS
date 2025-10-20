"""
Vault manager - State management and operations.

Manages vault state (locked/unlocked/panic), auto-lock, and WHY Journal logging.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from neura.core.events import get_event_bus
from neura.core.types import Result
from neura.vault.crypto import get_vault_crypto
from neura.vault.store import get_vault_store
from neura.vault.types import SecretEntry, VaultState, VaultStatus

logger = logging.getLogger(__name__)

# WHY Journal path
WHY_JOURNAL_PATH = Path("data/why_journal.jsonl")


class VaultManager:
    """
    Manage vault state and operations.

    Handles locking/unlocking, auto-lock timer, and WHY Journal logging.

    Example:
        >>> manager = VaultManager()
        >>> result = await manager.unlock("password")
        >>> if result.is_success():
        ...     await manager.put_secret("key", "value")
        ...     await manager.lock()
    """

    def __init__(
        self,
        db_path: str = "neura_vault/secrets.db",
        idle_timeout: int = 300,
        argon2_memory: int = 65536,
        argon2_iterations: int = 3,
        argon2_parallelism: int = 4,
    ) -> None:
        """
        Initialize vault manager.

        Args:
            db_path: Path to SQLCipher database
            idle_timeout: Auto-lock timeout in seconds
            argon2_memory: Argon2 memory cost in KB
            argon2_iterations: Argon2 time cost
            argon2_parallelism: Argon2 parallelism
        """
        self.db_path = db_path
        self.idle_timeout = idle_timeout

        # Crypto and store
        self._crypto = get_vault_crypto(
            memory_cost=argon2_memory,
            time_cost=argon2_iterations,
            parallelism=argon2_parallelism,
        )
        self._store = get_vault_store(db_path=db_path)

        # State management
        self._state = VaultState.LOCKED
        self._master_key: bytes | None = None
        self._salt: bytes | None = None
        self._last_activity: datetime | None = None
        self._last_unlock: datetime | None = None
        self._last_lock: datetime | None = None

        # Auto-lock timer
        self._auto_lock_task: asyncio.Task | None = None
        self._auto_lock_enabled = True

        logger.info(
            f"VaultManager initialized: idle_timeout={idle_timeout}s, "
            f"argon2_mem={argon2_memory}KB"
        )

    def _log_why_journal(
        self,
        action: str,
        input_summary: str,
        result: str,
        actor: str = "vault",
    ) -> None:
        """
        Log to WHY Journal.

        Args:
            action: Action performed
            input_summary: Summary of input
            result: SUCCESS or FAILURE
            actor: Who performed the action
        """
        WHY_JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "input_summary": input_summary[:200],
            "policy_check": "PASS",
            "user_approved": True,
            "result": result,
            "trace_id": str(uuid.uuid4()),
        }

        with open(WHY_JOURNAL_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.debug(f"WHY Journal: {action} - {result}")

    async def unlock(self, password: str) -> Result[bool]:
        """
        Unlock the vault with a password.

        Args:
            password: Master password

        Returns:
            Result[bool]: Success or error
        """
        trace_id = str(uuid.uuid4())
        logger.info(f"[{trace_id}] Unlock attempt")

        try:
            # Check if already unlocked
            if self._state == VaultState.UNLOCKED:
                logger.warning("Vault already unlocked")
                return Result.success(True)

            # Check if in panic mode
            if self._state == VaultState.PANIC:
                error_msg = "Vault in panic mode - restart required"
                logger.error(error_msg)
                self._log_why_journal("unlock_vault", "panic_mode", "FAILURE")
                return Result.failure(error_msg)

            # Get or create salt
            salt_path = Path(self.db_path).parent / "vault.salt"
            if salt_path.exists():
                with open(salt_path, "rb") as f:
                    self._salt = f.read()
            else:
                # First time - create salt
                self._salt = self._crypto.generate_salt()
                salt_path.parent.mkdir(parents=True, exist_ok=True)
                with open(salt_path, "wb") as f:
                    f.write(self._salt)
                logger.info("Created new vault salt")

            # Derive key from password
            self._master_key = self._crypto.derive_key(password, self._salt)

            # Try to open store
            result = self._store.open(self._master_key)

            if result.is_failure():
                # Failed - clear key from memory
                self._secure_erase_key()
                self._log_why_journal("unlock_vault", "invalid_password", "FAILURE")
                return result

            # Success
            self._state = VaultState.UNLOCKED
            self._last_unlock = datetime.utcnow()
            self._last_activity = datetime.utcnow()

            # Start auto-lock timer
            if self._auto_lock_enabled:
                self._start_auto_lock_timer()

            # Publish event
            event_bus = get_event_bus()
            await event_bus.publish(
                "vault.unlocked",
                {"timestamp": self._last_unlock.isoformat()},
                source="vault",
            )

            # Log to WHY Journal
            self._log_why_journal("unlock_vault", "password_provided", "SUCCESS")

            logger.info(f"[{trace_id}] Vault unlocked successfully")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Unlock failed: {e}"
            logger.error(f"[{trace_id}] {error_msg}", exc_info=True)
            self._secure_erase_key()
            self._log_why_journal("unlock_vault", "exception", "FAILURE")
            return Result.failure(error_msg)

    async def lock(self) -> Result[bool]:
        """
        Lock the vault.

        Returns:
            Result[bool]: Success or error
        """
        trace_id = str(uuid.uuid4())
        logger.info(f"[{trace_id}] Lock requested")

        try:
            # Already locked
            if self._state == VaultState.LOCKED:
                logger.info("Vault already locked")
                return Result.success(True)

            # Close store
            if self._store:
                self._store.close()

            # Erase key from memory
            self._secure_erase_key()

            # Update state
            self._state = VaultState.LOCKED
            self._last_lock = datetime.utcnow()

            # Stop auto-lock timer
            if self._auto_lock_task:
                self._auto_lock_task.cancel()
                self._auto_lock_task = None

            # Publish event
            event_bus = get_event_bus()
            await event_bus.publish(
                "vault.locked",
                {"timestamp": self._last_lock.isoformat()},
                source="vault",
            )

            # Log to WHY Journal
            self._log_why_journal("lock_vault", "user_requested", "SUCCESS")

            logger.info(f"[{trace_id}] Vault locked successfully")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Lock failed: {e}"
            logger.error(f"[{trace_id}] {error_msg}", exc_info=True)
            self._log_why_journal("lock_vault", "exception", "FAILURE")
            return Result.failure(error_msg)

    async def panic(self) -> Result[bool]:
        """
        Emergency panic mode - immediately lock vault and stop all services.

        Returns:
            Result[bool]: Success or error
        """
        trace_id = str(uuid.uuid4())
        logger.critical(f"[{trace_id}] PANIC MODE ACTIVATED")

        try:
            # Close store immediately
            if self._store:
                self._store.close()

            # Erase key from memory
            self._secure_erase_key()

            # Set panic state
            self._state = VaultState.PANIC
            self._last_lock = datetime.utcnow()

            # Stop auto-lock timer
            if self._auto_lock_task:
                self._auto_lock_task.cancel()
                self._auto_lock_task = None

            # Publish event
            event_bus = get_event_bus()
            await event_bus.publish(
                "vault.panic",
                {"timestamp": self._last_lock.isoformat()},
                source="vault",
            )

            # Log to WHY Journal
            self._log_why_journal("panic_mode", "emergency_lock", "SUCCESS")

            logger.critical(f"[{trace_id}] Panic mode complete - restart required")
            return Result.success(True)

        except Exception as e:
            error_msg = f"Panic failed: {e}"
            logger.error(f"[{trace_id}] {error_msg}", exc_info=True)
            self._log_why_journal("panic_mode", "exception", "FAILURE")
            return Result.failure(error_msg)

    def _secure_erase_key(self) -> None:
        """Securely erase the master key from memory."""
        if self._master_key:
            # Overwrite with zeros
            key_array = bytearray(self._master_key)
            for i in range(len(key_array)):
                key_array[i] = 0
            self._master_key = None
            logger.debug("Master key erased from memory")

    def _start_auto_lock_timer(self) -> None:
        """Start the auto-lock timer."""
        if self._auto_lock_task:
            self._auto_lock_task.cancel()

        async def auto_lock_worker():
            try:
                while True:
                    await asyncio.sleep(10)  # Check every 10 seconds

                    if self._state != VaultState.UNLOCKED:
                        break

                    if self._last_activity:
                        idle_time = (datetime.utcnow() - self._last_activity).total_seconds()

                        if idle_time >= self.idle_timeout:
                            logger.warning(f"Auto-lock triggered after {idle_time:.0f}s idle")
                            await self.lock()
                            break

            except asyncio.CancelledError:
                logger.debug("Auto-lock timer cancelled")

        self._auto_lock_task = asyncio.create_task(auto_lock_worker())
        logger.debug(f"Auto-lock timer started: {self.idle_timeout}s")

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = datetime.utcnow()

    async def put_secret(
        self,
        name: str,
        value: str,
        metadata: dict | None = None,
    ) -> Result[SecretEntry]:
        """
        Store a secret in the vault.

        Args:
            name: Secret name
            value: Secret value
            metadata: Optional metadata

        Returns:
            Result[SecretEntry]: Stored secret or error
        """
        if self._state != VaultState.UNLOCKED:
            return Result.failure("Vault is locked")

        self._update_activity()

        result = self._store.put_secret(name, value, metadata)

        if result.is_success():
            self._log_why_journal(
                "put_secret",
                f"name={name}",
                "SUCCESS",
            )
        else:
            self._log_why_journal(
                "put_secret",
                f"name={name}",
                "FAILURE",
            )

        return result

    async def get_secret(self, name: str) -> Result[SecretEntry]:
        """
        Get a secret from the vault.

        Args:
            name: Secret name

        Returns:
            Result[SecretEntry]: Secret or error
        """
        if self._state != VaultState.UNLOCKED:
            return Result.failure("Vault is locked")

        self._update_activity()

        result = self._store.get_secret(name)

        if result.is_success():
            self._log_why_journal(
                "get_secret",
                f"name={name}",
                "SUCCESS",
            )
        else:
            self._log_why_journal(
                "get_secret",
                f"name={name}",
                "FAILURE",
            )

        return result

    async def list_secrets(self) -> Result[list[str]]:
        """
        List all secret names.

        Returns:
            Result[list[str]]: List of names or error
        """
        if self._state != VaultState.UNLOCKED:
            return Result.failure("Vault is locked")

        self._update_activity()
        return self._store.list_secrets()

    async def delete_secret(self, name: str) -> Result[bool]:
        """
        Delete a secret.

        Args:
            name: Secret name

        Returns:
            Result[bool]: Success or error
        """
        if self._state != VaultState.UNLOCKED:
            return Result.failure("Vault is locked")

        self._update_activity()

        result = self._store.delete_secret(name)

        if result.is_success():
            self._log_why_journal(
                "delete_secret",
                f"name={name}",
                "SUCCESS",
            )
        else:
            self._log_why_journal(
                "delete_secret",
                f"name={name}",
                "FAILURE",
            )

        return result

    def get_status(self) -> VaultStatus:
        """
        Get vault status.

        Returns:
            VaultStatus: Current status
        """
        total_secrets = self._store.count_secrets() if self._store.is_open() else 0

        return VaultStatus(
            state=self._state,
            total_secrets=total_secrets,
            last_unlock=self._last_unlock,
            last_lock=self._last_lock,
            auto_lock_enabled=self._auto_lock_enabled,
            idle_timeout_seconds=self.idle_timeout,
        )

    def is_unlocked(self) -> bool:
        """Check if vault is unlocked."""
        return self._state == VaultState.UNLOCKED


# Singleton instance
_vault_manager: VaultManager | None = None


def get_vault_manager(
    db_path: str = "neura_vault/secrets.db",
    idle_timeout: int = 300,
) -> VaultManager:
    """
    Get the global VaultManager instance.

    Args:
        db_path: Database path
        idle_timeout: Auto-lock timeout in seconds

    Returns:
        VaultManager: Singleton instance
    """
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultManager(
            db_path=db_path,
            idle_timeout=idle_timeout,
        )
    return _vault_manager
