"""
Vault API router - FastAPI endpoints for vault operations.

Provides REST endpoints for unlocking, locking, and managing secrets.
"""

import logging

from fastapi import APIRouter, HTTPException

from neura.vault.manager import get_vault_manager
from neura.vault.types import (
    GetSecretResponse,
    PutSecretRequest,
    UnlockRequest,
    VaultStatus,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/unlock")
async def unlock_vault(request: UnlockRequest) -> dict:
    """
    Unlock the vault with a password.

    Args:
        request: Unlock request with password

    Returns:
        dict: Success message

    Raises:
        HTTPException: If unlock fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/vault/unlock \
          -H "Content-Type: application/json" \
          -d '{"password": "my_secure_password"}'
        ```
    """
    logger.info("Unlock request received")

    manager = get_vault_manager()

    # Get password from SecretStr
    password = request.password.get_secret_value()

    result = await manager.unlock(password)

    if result.is_failure():
        logger.error(f"Unlock failed: {result.error}")
        raise HTTPException(status_code=401, detail=result.error)

    return {"message": "Vault unlocked successfully"}


@router.post("/lock")
async def lock_vault() -> dict:
    """
    Lock the vault.

    Returns:
        dict: Success message

    Raises:
        HTTPException: If lock fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/vault/lock
        ```
    """
    logger.info("Lock request received")

    manager = get_vault_manager()
    result = await manager.lock()

    if result.is_failure():
        logger.error(f"Lock failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return {"message": "Vault locked successfully"}


@router.post("/panic")
async def panic_vault() -> dict:
    """
    Emergency panic mode - immediately lock vault.

    Returns:
        dict: Success message

    Raises:
        HTTPException: If panic fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/vault/panic
        ```
    """
    logger.critical("PANIC request received")

    manager = get_vault_manager()
    result = await manager.panic()

    if result.is_failure():
        logger.error(f"Panic failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return {"message": "Panic mode activated - vault locked"}


@router.post("/put")
async def put_secret(request: PutSecretRequest) -> dict:
    """
    Store a secret in the vault.

    Args:
        request: Put secret request

    Returns:
        dict: Success message with secret name

    Raises:
        HTTPException: If vault is locked or operation fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/vault/put \
          -H "Content-Type: application/json" \
          -d '{
            "name": "api_key",
            "value": "secret_value_here",
            "metadata": {"description": "My API key"}
          }'
        ```
    """
    logger.info(f"Put secret request: {request.name}")

    manager = get_vault_manager()

    if not manager.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")

    # Get value from SecretStr
    value = request.value.get_secret_value()

    result = await manager.put_secret(
        name=request.name,
        value=value,
        metadata=request.metadata,
    )

    if result.is_failure():
        logger.error(f"Put secret failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return {"message": f"Secret '{request.name}' stored successfully"}


@router.get("/get")
async def get_secret(name: str) -> GetSecretResponse:
    """
    Get a secret from the vault.

    Args:
        name: Secret name

    Returns:
        GetSecretResponse: Secret data

    Raises:
        HTTPException: If vault is locked or secret not found

    Example:
        ```bash
        curl http://localhost:8000/api/vault/get?name=api_key
        ```
    """
    logger.info(f"Get secret request: {name}")

    manager = get_vault_manager()

    if not manager.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")

    result = await manager.get_secret(name)

    if result.is_failure():
        logger.error(f"Get secret failed: {result.error}")
        raise HTTPException(status_code=404, detail=result.error)

    entry = result.data

    return GetSecretResponse(
        name=entry.name,
        value=entry.value.get_secret_value(),
        metadata=entry.metadata,
    )


@router.get("/list")
async def list_secrets() -> list[str]:
    """
    List all secret names.

    Returns:
        List[str]: List of secret names

    Raises:
        HTTPException: If vault is locked

    Example:
        ```bash
        curl http://localhost:8000/api/vault/list
        ```
    """
    logger.info("List secrets request")

    manager = get_vault_manager()

    if not manager.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")

    result = await manager.list_secrets()

    if result.is_failure():
        logger.error(f"List secrets failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@router.delete("/delete")
async def delete_secret(name: str) -> dict:
    """
    Delete a secret from the vault.

    Args:
        name: Secret name

    Returns:
        dict: Success message

    Raises:
        HTTPException: If vault is locked or secret not found

    Example:
        ```bash
        curl -X DELETE http://localhost:8000/api/vault/delete?name=api_key
        ```
    """
    logger.info(f"Delete secret request: {name}")

    manager = get_vault_manager()

    if not manager.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")

    result = await manager.delete_secret(name)

    if result.is_failure():
        logger.error(f"Delete secret failed: {result.error}")
        raise HTTPException(status_code=404, detail=result.error)

    return {"message": f"Secret '{name}' deleted successfully"}


@router.get("/status", response_model=VaultStatus)
async def get_vault_status() -> VaultStatus:
    """
    Get vault status.

    Returns:
        VaultStatus: Current vault status

    Example:
        ```bash
        curl http://localhost:8000/api/vault/status
        ```
    """
    logger.debug("Status request")

    manager = get_vault_manager()
    return manager.get_status()


@router.get("/")
async def vault_info() -> dict:
    """
    Get Vault module information.

    Returns:
        dict: Module information
    """
    return {
        "module": "vault",
        "status": "operational",
        "description": "Encrypted secrets management with SQLCipher",
        "endpoints": {
            "unlock": "/api/vault/unlock",
            "lock": "/api/vault/lock",
            "panic": "/api/vault/panic",
            "put": "/api/vault/put",
            "get": "/api/vault/get",
            "list": "/api/vault/list",
            "delete": "/api/vault/delete",
            "status": "/api/vault/status",
        },
    }
