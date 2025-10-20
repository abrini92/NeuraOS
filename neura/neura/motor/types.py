"""
Motor types - Pydantic models for local automation.

Defines actions, results, and validation rules.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """Supported action types."""

    TYPE_TEXT = "type_text"
    CLICK = "click"
    OPEN_APP = "open_app"
    EXECUTE_COMMAND = "execute_command"  # BLOCKED by default


class OSType(str, Enum):
    """Supported operating systems."""

    MAC = "mac"
    LINUX = "linux"


class MotorAction(BaseModel):
    """
    Motor action request.

    Attributes:
        app: Target application name
        action: Type of action to perform
        text: Text to type (for type_text)
        x: X coordinate (for click)
        y: Y coordinate (for click)
        critical: Whether action requires user confirmation
        os: Target OS (auto-detected if None)
        meta: Additional metadata
    """

    app: str | None = Field(None, description="Target application")
    action: ActionType = Field(..., description="Action type")
    text: str | None = Field(None, description="Text to type")
    x: int | None = Field(None, description="X coordinate for click")
    y: int | None = Field(None, description="Y coordinate for click")
    critical: bool = Field(False, description="Requires user confirmation")
    os: OSType | None = Field(None, description="Target OS")
    meta: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str | None) -> str | None:
        """Validate text doesn't contain dangerous patterns."""
        if v is None:
            return v

        # Check for blocked patterns
        blocked = ["rm -rf", "curl | bash", "sudo ", "DROP TABLE", "/etc/", "/System/"]
        for pattern in blocked:
            if pattern in v:
                raise ValueError(f"Text contains blocked pattern: {pattern}")

        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: ActionType) -> ActionType:
        """Validate action type."""
        if v == ActionType.EXECUTE_COMMAND:
            raise ValueError("execute_command is blocked by default for security")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Validate required fields per action
        if self.action == ActionType.TYPE_TEXT and not self.text:
            raise ValueError("text is required for type_text action")

        if self.action == ActionType.CLICK and (self.x is None or self.y is None):
            raise ValueError("x and y coordinates required for click action")

        if self.action == ActionType.OPEN_APP and not self.app:
            raise ValueError("app is required for open_app action")


class MotorStatus(str, Enum):
    """Motor execution status."""

    SUCCESS = "SUCCESS"
    BLOCKED = "BLOCKED"
    FAILURE = "FAILURE"


class MotorResult(BaseModel):
    """
    Motor execution result.

    Attributes:
        status: Execution status
        reason: Success/failure/block reason
        duration_ms: Execution duration in milliseconds
        trace_id: Unique trace ID for WHY Journal correlation
        action: Original action that was executed
    """

    status: MotorStatus = Field(..., description="Execution status")
    reason: str = Field(..., description="Status reason")
    duration_ms: float = Field(..., description="Duration in ms")
    trace_id: str = Field(..., description="Trace ID")
    action: MotorAction | None = Field(None, description="Original action")

    class Config:
        use_enum_values = True
