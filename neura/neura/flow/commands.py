"""
Flow commands - Command registry and built-in commands.

Handles command parsing, execution, and routing.
"""

import logging
from collections.abc import Awaitable, Callable

import httpx

from neura.flow.types import FlowCommand, FlowResponse, FlowSession
from neura.flow.ui import get_ui

logger = logging.getLogger(__name__)

# Type alias for command handlers
CommandHandler = Callable[[FlowCommand, FlowSession], Awaitable[FlowResponse]]


class CommandRegistry:
    """
    Registry of all available commands.

    Maps command names to their handler functions.
    """

    def __init__(self, api_base: str = "http://localhost:8000") -> None:
        """
        Initialize command registry.

        Args:
            api_base: Base URL for Neura API
        """
        self.api_base = api_base
        self.ui = get_ui()
        self.handlers: dict[str, CommandHandler] = {}

        # Register built-in commands
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in command handlers."""
        self.handlers = {
            "help": self.cmd_help,
            "ask": self.cmd_ask,
            "remember": self.cmd_remember,
            "recall": self.cmd_recall,
            "vault": self.cmd_vault,
            "motor": self.cmd_motor,
            "policy": self.cmd_policy,
            "why": self.cmd_why,
            "status": self.cmd_status,
            "applescript": self.cmd_applescript,  # AppleScript automation
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "chat": self.cmd_chat,  # Natural language fallback
        }

    async def execute(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Execute a command.

        Args:
            command: Parsed command
            session: Current session

        Returns:
            FlowResponse: Command response
        """
        handler = self.handlers.get(command.name)

        if not handler:
            return FlowResponse(
                content=f"Unknown command: /{command.name}\nType /help for available commands.",
                source="Flow",
                success=False,
            )

        try:
            response = await handler(command, session)
            session.increment_commands()
            return response
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return FlowResponse(
                content=f"Error executing command: {str(e)}", source="Flow", success=False
            )

    # ========== Built-in Command Handlers ==========

    async def cmd_help(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /help command."""
        self.ui.print_help()
        return FlowResponse(
            content="",  # UI already printed
            source="Flow",
            success=True,
        )

    async def cmd_ask(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /ask command - question to Cortex with streaming.

        Example: /ask What is consciousness?
        """
        if not command.args:
            return FlowResponse(content="Usage: /ask <question>", source="Flow", success=False)

        question = command.args[0]

        try:
            # Use streaming for better UX
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/api/cortex/stream",
                    json={"prompt": question},
                ) as response:
                    if response.status_code != 200:
                        return FlowResponse(
                            content=f"Cortex error: {response.status_code}",
                            source="Cortex",
                            success=False
                        )
                    
                    # Collect streamed response
                    full_text = ""
                    self.ui.console.print("\n[blue]Neura:[/blue] ", end="")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]  # Remove "data: " prefix
                            
                            if chunk == "[DONE]":
                                break
                            elif chunk.startswith("[ERROR]"):
                                self.ui.console.print(f"\n[red]{chunk}[/red]")
                                break
                            else:
                                # Display chunk in real-time
                                self.ui.console.print(chunk, end="")
                                full_text += chunk
                    
                    self.ui.console.print("\n")  # New line after streaming
                    
                    # Add to conversation history
                    session.add_message("user", question)
                    session.add_message("assistant", full_text)

                    return FlowResponse(content=full_text, source="Cortex", success=True)

        except httpx.ConnectError:
            return FlowResponse(
                content="Cannot connect to Neura API. Is it running?", source="Flow", success=False
            )
        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_remember(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /remember command - store in memory.

        Example: /remember Important deadline: Nov 15
        """
        if not command.args:
            return FlowResponse(content="Usage: /remember <text>", source="Flow", success=False)

        content = command.args[0]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/memory/store", json={"content": content}
                )

                if response.status_code == 200:
                    data = response.json()
                    memory_id = data.get("id", "unknown")

                    return FlowResponse(
                        content=f"✓ Stored in memory (id: {memory_id})",
                        source="Memory",
                        success=True,
                    )
                else:
                    return FlowResponse(
                        content=f"Memory error: {response.text}", source="Memory", success=False
                    )

        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_recall(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /recall command - search memory.

        Example: /recall project deadline
        """
        if not command.args:
            return FlowResponse(content="Usage: /recall <query>", source="Flow", success=False)

        query = command.args[0]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/memory/recall", json={"query": query, "k": 5}
                )

                if response.status_code == 200:
                    results = response.json()

                    # Use UI to display results
                    self.ui.print_memory_results(results)

                    return FlowResponse(
                        content="",  # UI already printed
                        source="Memory",
                        success=True,
                    )
                else:
                    return FlowResponse(
                        content=f"Memory error: {response.text}", source="Memory", success=False
                    )

        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_vault(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /vault command.

        Example: /vault status
        """
        if not command.args:
            return FlowResponse(
                content="Usage: /vault <unlock|lock|status>", source="Flow", success=False
            )

        subcmd = command.args[0].lower()

        try:
            async with httpx.AsyncClient() as client:
                if subcmd == "status":
                    response = await client.get(f"{self.api_base}/api/vault/status")

                    if response.status_code == 200:
                        data = response.json()
                        state = data.get("state", "unknown")
                        total = data.get("total_secrets", 0)

                        return FlowResponse(
                            content=f"Vault Status: **{state}**\nSecrets: {total}",
                            source="Vault",
                            success=True,
                        )

                else:
                    return FlowResponse(
                        content=f"Vault command '{subcmd}' not implemented in Flow yet.\nUse: neura vault {subcmd}",
                        source="Flow",
                        success=False,
                    )

        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_motor(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /motor command."""
        return FlowResponse(
            content="Motor commands not yet implemented in Flow.\nUse: neura motor --help",
            source="Flow",
            success=False,
        )

    async def cmd_policy(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /policy command."""
        return FlowResponse(
            content="Policy commands not yet implemented in Flow.\nUse: neura policy --help",
            source="Flow",
            success=False,
        )

    async def cmd_why(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /why command - WHY Journal.

        Example: /why
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get latest entries
                response = await client.get(f"{self.api_base}/api/why/?limit=10")

                if response.status_code == 200:
                    entries = response.json()

                    # Use UI to display entries
                    self.ui.print_why_entries(entries)

                    return FlowResponse(
                        content="",  # UI already printed
                        source="WHY",
                        success=True,
                    )
                else:
                    return FlowResponse(
                        content=f"WHY Journal error: {response.text}", source="WHY", success=False
                    )

        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_status(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle /status command - system health.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/api/health")

                if response.status_code == 200:
                    data = response.json()

                    # Use UI to display status
                    self.ui.print_status(data)

                    return FlowResponse(
                        content="",  # UI already printed
                        source="Flow",
                        success=True,
                    )
                else:
                    return FlowResponse(
                        content=f"Health check failed: {response.text}",
                        source="Flow",
                        success=False,
                    )

        except httpx.ConnectError:
            return FlowResponse(
                content="Cannot connect to Neura API. Is it running?", source="Flow", success=False
            )
        except Exception as e:
            return FlowResponse(content=f"Error: {str(e)}", source="Flow", success=False)

    async def cmd_applescript(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /applescript command - execute AppleScript automation."""
        try:
            from neura.flow.applescript_commands import AppleScriptFlowHandler

            if len(command.args) < 2:
                return FlowResponse(
                    content="Usage: /applescript <category> <operation> [args]\nCategories: finder, system, safari, notes",
                    source="AppleScript",
                    success=False,
                )

            category = command.args[0]
            operation = command.args[1]
            args = " ".join(command.args[2:]) if len(command.args) > 2 else ""

            handler = AppleScriptFlowHandler()
            result = await handler.execute(category, operation, args)

            if result.is_success():
                return FlowResponse(content=result.data, source="AppleScript", success=True)
            else:
                return FlowResponse(
                    content=f"AppleScript error: {result.error}",
                    source="AppleScript",
                    success=False,
                )

        except Exception as e:
            logger.error(f"AppleScript command error: {e}")
            return FlowResponse(content=f"Error: {str(e)}", source="AppleScript", success=False)

    async def cmd_clear(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /clear command - clear screen."""
        self.ui.clear_screen()
        return FlowResponse(content="", source="Flow", success=True)

    async def cmd_exit(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """Handle /exit command - exit REPL."""
        return FlowResponse(
            content="__EXIT__",  # Special marker for REPL
            source="Flow",
            success=True,
        )

    async def cmd_chat(self, command: FlowCommand, session: FlowSession) -> FlowResponse:
        """
        Handle natural language input - send to Cortex.

        This is the fallback for non-command input.
        """
        if not command.args:
            return FlowResponse(content="", source="Flow", success=True)

        # Use /ask handler for natural language
        return await self.cmd_ask(command, session)
