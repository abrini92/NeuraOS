"""
Flow types - Models for interactive TUI session.

Defines Pydantic models for Flow REPL state and commands.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Type of command."""

    BUILTIN = "builtin"  # /help, /ask, etc.
    NATURAL = "natural"  # Natural language → Cortex


class FlowCommand(BaseModel):
    """
    Parsed command from user input.

    Example:
        >>> cmd = FlowCommand(
        ...     raw="/ask What is consciousness?",
        ...     type=CommandType.BUILTIN,
        ...     name="ask",
        ...     args=["What is consciousness?"]
        ... )
    """

    raw: str = Field(..., description="Raw user input")
    type: CommandType = Field(..., description="Command type")
    name: str = Field(..., description="Command name (without /)")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    kwargs: dict[str, Any] = Field(default_factory=dict, description="Named arguments")

    @classmethod
    def parse(cls, user_input: str) -> "FlowCommand":
        """
        Parse user input into FlowCommand.

        Args:
            user_input: Raw user input

        Returns:
            FlowCommand: Parsed command

        Example:
            >>> FlowCommand.parse("/ask What is AI?")
            FlowCommand(raw="/ask What is AI?", type="builtin", name="ask", args=["What is AI?"])

            >>> FlowCommand.parse("Hello, how are you?")
            FlowCommand(raw="Hello, how are you?", type="natural", name="chat", args=["Hello, how are you?"])
        """
        user_input = user_input.strip()

        if not user_input:
            return cls(raw="", type=CommandType.NATURAL, name="chat", args=[])

        # Built-in command (starts with /)
        if user_input.startswith("/"):
            parts = user_input[1:].split(maxsplit=1)
            name = parts[0].lower()
            args = [parts[1]] if len(parts) > 1 else []

            return cls(raw=user_input, type=CommandType.BUILTIN, name=name, args=args)

        # Natural language
        return cls(raw=user_input, type=CommandType.NATURAL, name="chat", args=[user_input])


class FlowResponse(BaseModel):
    """
    Response to display to user.

    Attributes:
        content: Response content (markdown supported)
        source: Source of response (e.g., "Cortex", "Memory")
        success: Whether operation succeeded
        metadata: Additional metadata to display
    """

    content: str = Field(..., description="Response content")
    source: str = Field(default="Flow", description="Response source")
    success: bool = Field(default=True, description="Success status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    def is_error(self) -> bool:
        """Check if response is an error."""
        return not self.success


class ConversationMessage(BaseModel):
    """Single message in conversation history."""

    role: str = Field(..., description="Role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When message was sent"
    )


class FlowSession(BaseModel):
    """
    State of interactive Flow session.

    Manages conversation history, context window, and session metadata.
    """

    session_id: str = Field(..., description="Unique session ID")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list, description="Full conversation history"
    )
    context_window_size: int = Field(default=2048, description="Max context tokens")
    commands_executed: int = Field(default=0, description="Number of commands executed")

    def add_message(self, role: str, content: str) -> None:
        """
        Add message to conversation history.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        message = ConversationMessage(role=role, content=content)
        self.conversation_history.append(message)

    def get_recent_context(self, max_messages: int = 10) -> list[ConversationMessage]:
        """
        Get recent conversation context.

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self.conversation_history[-max_messages:]

    def get_context_for_cortex(self, max_messages: int = 10) -> list[dict[str, str]]:
        """
        Get conversation context formatted for Cortex API.

        Returns:
            List of messages in Cortex format
        """
        recent = self.get_recent_context(max_messages)
        return [{"role": msg.role, "content": msg.content} for msg in recent]

    def increment_commands(self) -> None:
        """Increment command counter."""
        self.commands_executed += 1


class FlowConfig(BaseModel):
    """Configuration for Flow REPL."""

    save_history: bool = Field(default=True, description="Save command history")
    history_file: str = Field(default="~/.neura/flow_history.txt", description="History file path")
    max_history: int = Field(default=1000, description="Max history entries")
    context_window: int = Field(default=2048, description="Context window size")
    auto_save_conversations: bool = Field(default=True, description="Auto-save to memory")
    enable_auto_completion: bool = Field(default=True, description="Enable tab completion")
