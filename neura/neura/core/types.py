"""
Shared types used across all Neura modules.

This module defines common types like Result, Event, and configuration
structures that are used throughout the system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ResultStatus(str, Enum):
    """Status of a Result operation."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class Result(Generic[T]):
    """
    Result type for operations that can succeed or fail.

    This provides explicit error handling without exceptions,
    following the principle of "fail loudly".

    Args:
        status: Success or failure status
        data: The result data if successful
        error: Error message if failed

    Example:
        >>> result = Result.success({"key": "value"})
        >>> if result.is_success():
        ...     print(result.data)
    """

    status: ResultStatus
    data: T | None = None
    error: str | None = None

    @staticmethod
    def success(data: T) -> "Result[T]":
        """Create a successful result."""
        return Result(status=ResultStatus.SUCCESS, data=data)

    @staticmethod
    def failure(error: str) -> "Result[T]":
        """Create a failed result."""
        return Result(status=ResultStatus.FAILURE, error=error)

    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self.status == ResultStatus.SUCCESS

    def is_failure(self) -> bool:
        """Check if the result failed."""
        return self.status == ResultStatus.FAILURE

    def unwrap(self) -> T:
        """
        Unwrap the result data or raise if failed.

        Raises:
            ValueError: If the result is a failure
        """
        if self.is_failure():
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.data  # type: ignore


@dataclass
class Event:
    """
    Event structure for the internal event bus.

    Events allow modules to communicate asynchronously without
    direct dependencies.

    Args:
        name: Event name (e.g., "memory.stored", "cortex.generated")
        data: Event payload
        timestamp: When the event occurred
        source: Module that emitted the event
    """

    name: str
    data: dict[str, Any]
    timestamp: datetime
    source: str

    @staticmethod
    def create(name: str, data: dict[str, Any], source: str) -> "Event":
        """Create a new event with current timestamp."""
        return Event(
            name=name,
            data=data,
            timestamp=datetime.utcnow(),
            source=source,
        )


@dataclass
class Config:
    """
    Global configuration structure.

    This will be expanded as modules are added.
    """

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Paths
    data_dir: str = "./data"
    logs_dir: str = "./logs"
    vault_dir: str = "./neura_vault"

    # Debug
    debug: bool = False
    log_level: str = "INFO"
