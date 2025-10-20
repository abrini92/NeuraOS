"""
Custom exceptions for Neura.

All exceptions should inherit from NeuraError for consistent error handling.
Each module should define its own specific exceptions.
"""


class NeuraError(Exception):
    """Base exception for all Neura errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        Initialize a Neura error.

        Args:
            message: Human-readable error message
            details: Optional additional context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# region Core Exceptions


class CoreError(NeuraError):
    """Base exception for core module errors."""

    pass


class APIError(CoreError):
    """API-related errors."""

    pass


class EventBusError(CoreError):
    """Event bus errors."""

    pass


class ConfigError(CoreError):

    def user_friendly_message(self) -> str:
        """Get user-friendly message."""
        return f"I couldn't connect. {self.message}\n\n💡 {self.suggestion or 'Is the service running?'}"


class VoiceError(NeuraError):
    """Voice module errors."""

    pass


class MotorError(NeuraError):
    """Motor module errors."""

    pass


# endregion
