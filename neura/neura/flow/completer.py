"""
Flow completer - Auto-completion for Flow REPL.

Provides intelligent command and argument completion using prompt-toolkit.
"""

import logging
from collections.abc import Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

logger = logging.getLogger(__name__)


class FlowCompleter(Completer):
    """
    Auto-completion for Flow REPL commands.

    Provides tab-completion for:
    - Built-in commands (/help, /ask, etc.)
    - Command arguments
    - Natural language (no completion)
    """

    def __init__(self) -> None:
        """Initialize completer with available commands."""
        # Built-in commands
        self.commands = [
            "/help",
            "/ask",
            "/remember",
            "/recall",
            "/vault",
            "/motor",
            "/policy",
            "/why",
            "/status",
            "/clear",
            "/exit",
        ]

        # Command arguments/subcommands
        self.command_args = {
            "/vault": ["unlock", "lock", "status"],
            "/motor": ["type_text", "click", "open_app"],
            "/policy": ["validate"],
            "/why": ["--stats", "--actor", "--result"],
        }

        # Command descriptions
        self.descriptions = {
            "/help": "Show help message",
            "/ask": "Ask Cortex a question",
            "/remember": "Store something in memory",
            "/recall": "Search memory",
            "/vault": "Vault operations",
            "/motor": "Execute motor action",
            "/policy": "Check policy",
            "/why": "View WHY Journal",
            "/status": "System health check",
            "/clear": "Clear screen",
            "/exit": "Exit Flow shell",
        }

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Get completions for current document.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor

        # If text doesn't start with /, no completion (natural language)
        if not text.startswith("/"):
            return

        # Split into command and args
        parts = text.split()

        if len(parts) == 0:
            # Empty, suggest all commands
            yield from self._complete_commands("")

        elif len(parts) == 1:
            # Completing command name
            word = parts[0]
            yield from self._complete_commands(word)

        else:
            # Completing arguments
            command = parts[0]
            current_word = parts[-1] if not text.endswith(" ") else ""

            yield from self._complete_args(command, current_word)

    def _complete_commands(self, prefix: str) -> Iterable[Completion]:
        """
        Complete command names.

        Args:
            prefix: Current prefix

        Yields:
            Command completions
        """
        for cmd in self.commands:
            if cmd.startswith(prefix):
                # Calculate start position for replacement
                start_position = -len(prefix)

                yield Completion(
                    text=cmd,
                    start_position=start_position,
                    display=cmd,
                    display_meta=self.descriptions.get(cmd, ""),
                )

    def _complete_args(self, command: str, prefix: str) -> Iterable[Completion]:
        """
        Complete command arguments.

        Args:
            command: Command name
            prefix: Current argument prefix

        Yields:
            Argument completions
        """
        args = self.command_args.get(command, [])

        for arg in args:
            if arg.startswith(prefix):
                start_position = -len(prefix)

                yield Completion(text=arg, start_position=start_position, display=arg)


def create_completer() -> FlowCompleter:
    """
    Create and return a FlowCompleter instance.

    Returns:
        FlowCompleter: Configured completer
    """
    return FlowCompleter()
