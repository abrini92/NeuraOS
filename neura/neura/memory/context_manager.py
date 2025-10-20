"""
Context manager for conversational memory.

Manages a sliding window of conversation history with automatic summarization
when the context exceeds token limits.
"""

import logging

from neura.memory.types import ContextWindow

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manage conversational context with sliding window.

    Automatically summarizes old context when window exceeds token limit.

    Example:
        >>> manager = ContextManager(max_tokens=4096)
        >>> manager.add_message("user", "Hello!")
        >>> manager.add_message("assistant", "Hi there!")
        >>> context = manager.get_context()
    """

    def __init__(self, max_tokens: int = 4096) -> None:
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum tokens in context window
        """
        self.max_tokens = max_tokens
        self._window = ContextWindow(
            messages=[],
            max_tokens=max_tokens,
            current_tokens=0,
            summary=None,
        )
        logger.info(f"ContextManager initialized: max_tokens={max_tokens}")

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the context window.

        Args:
            role: Message role ("user", "assistant", "system")
            content: Message content

        Example:
            >>> manager.add_message("user", "What is Neura?")
            >>> manager.add_message("assistant", "Neura is a cognitive OS")
        """
        message = {"role": role, "content": content}

        # Estimate tokens (rough: ~4 chars per token)
        tokens = len(content) // 4

        # Check if we need to summarize
        if self._window.current_tokens + tokens > self.max_tokens:
            logger.info("Context window full, summarizing old context")
            self._summarize_old_context()

        self._window.messages.append(message)
        self._window.current_tokens += tokens

        logger.debug(
            f"Added message: role={role}, tokens={tokens}, total={self._window.current_tokens}"
        )

    def get_context(
        self,
        max_tokens: int | None = None,
        include_summary: bool = True,
    ) -> list[dict[str, str]]:
        """
        Get the current context for LLM consumption.

        Args:
            max_tokens: Optional override for max tokens
            include_summary: Whether to include summary as system message

        Returns:
            List of messages for LLM context

        Example:
            >>> context = manager.get_context(max_tokens=2048)
            >>> for msg in context:
            ...     print(f"{msg['role']}: {msg['content'][:50]}")
        """
        effective_max = max_tokens or self.max_tokens
        messages = []

        # Add summary if available
        if include_summary and self._window.summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"Previous conversation summary:\n{self._window.summary}",
                }
            )

        # Add recent messages within token limit
        current_tokens = 0
        for msg in reversed(self._window.messages):
            msg_tokens = len(msg["content"]) // 4
            if current_tokens + msg_tokens > effective_max:
                break
            messages.insert(0, msg)
            current_tokens += msg_tokens

        logger.debug(f"Get context: {len(messages)} messages, ~{current_tokens} tokens")
        return messages

    def _summarize_old_context(self) -> None:
        """
        Summarize old context to free up token space.

        This is a placeholder for now. In production, this would call
        the Cortex to generate a summary of old messages.
        """
        # Keep only the last 50% of messages
        keep_count = len(self._window.messages) // 2

        # Messages to summarize
        to_summarize = self._window.messages[:-keep_count] if keep_count > 0 else []

        if to_summarize:
            # Simple summary (placeholder - should use Cortex in production)
            summary_parts = []
            for msg in to_summarize:
                summary_parts.append(f"{msg['role']}: {msg['content'][:100]}...")

            new_summary = "\n".join(summary_parts[-10:])  # Last 10 messages

            if self._window.summary:
                self._window.summary = f"{self._window.summary}\n\n{new_summary}"
            else:
                self._window.summary = new_summary

            # Keep only recent messages
            self._window.messages = self._window.messages[-keep_count:] if keep_count > 0 else []

            # Recalculate tokens
            self._window.current_tokens = sum(
                len(msg["content"]) // 4 for msg in self._window.messages
            )

            logger.info(
                f"Summarized {len(to_summarize)} old messages, "
                f"kept {len(self._window.messages)} recent"
            )

    def clear(self) -> None:
        """Clear all context and summary."""
        self._window.messages.clear()
        self._window.current_tokens = 0
        self._window.summary = None
        logger.info("Context cleared")

    def get_summary(self) -> str | None:
        """Get the current summary of old context."""
        return self._window.summary

    def get_message_count(self) -> int:
        """Get the number of messages in the window."""
        return len(self._window.messages)

    def get_token_count(self) -> int:
        """Get the approximate token count."""
        return self._window.current_tokens

    def export(self) -> ContextWindow:
        """Export the current context window."""
        return self._window.copy(deep=True)

    def import_context(self, window: ContextWindow) -> None:
        """Import a context window."""
        self._window = window.copy(deep=True)
        logger.info(f"Imported context: {len(self._window.messages)} messages")


# Singleton instance
_context_manager: ContextManager | None = None


def get_context_manager(max_tokens: int = 4096) -> ContextManager:
    """
    Get the global context manager instance.

    Args:
        max_tokens: Maximum tokens in window

    Returns:
        ContextManager: Singleton instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager(max_tokens=max_tokens)
    return _context_manager
