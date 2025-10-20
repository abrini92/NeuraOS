"""
Flow UI - Rich-based user interface for Flow REPL.

Provides formatted output using Rich library.
"""

import logging
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)

# Global console instance
console = Console()


class FlowUI:
    """
    Rich-based UI for Flow REPL.

    Handles all visual output formatting.
    """

    def __init__(self) -> None:
        """Initialize FlowUI."""
        self.console = console

    def print_welcome(self) -> None:
        """Print welcome banner."""
        banner = Text()
        banner.append("\n")
        banner.append("╔═══════════════════════════════════════╗\n", style="cyan bold")
        banner.append("║    ", style="cyan bold")
        banner.append("🧠 NEURA OS - Flow Shell", style="white bold")
        banner.append("      ║\n", style="cyan bold")
        banner.append("║  ", style="cyan bold")
        banner.append("Local-First Cognitive Interface", style="dim")
        banner.append("  ║\n", style="cyan bold")
        banner.append("╚═══════════════════════════════════════╝\n", style="cyan bold")
        banner.append("\n")
        banner.append("Type ", style="dim")
        banner.append("/help", style="cyan")
        banner.append(" for commands, or just talk naturally.\n", style="dim")
        banner.append("\n")

        self.console.print(banner)

    def print_goodbye(self) -> None:
        """Print goodbye message."""
        self.console.print("\n[cyan bold]Goodbye![/cyan bold] 👋\n")

    def print_help(self) -> None:
        """Print help table with all commands."""
        table = Table(title="[cyan bold]Available Commands[/cyan bold]", show_header=True)
        table.add_column("Command", style="cyan", width=20)
        table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/ask <question>", "Ask Cortex a question"),
            ("/remember <text>", "Store something in memory"),
            ("/recall <query>", "Search memory"),
            ("/vault <cmd>", "Vault operations (unlock/lock/status)"),
            ("/motor <action>", "Execute motor action"),
            ("/policy <action>", "Check policy validation"),
            ("/why [filters]", "View WHY Journal"),
            ("/status", "System health check"),
            ("/applescript <app> <op>", "🍎 AppleScript automation (macOS)"),
            ("/clear", "Clear screen"),
            ("/exit", "Exit Flow shell"),
            ("", ""),
            (
                "[dim]Voice commands[/dim]",
                "[dim]'list files', 'battery level', 'open folder'[/dim]",
            ),
            ("[dim]Natural language[/dim]", "[dim]Just type to chat with Cortex[/dim]"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def print_response(
        self, content: str, source: str = "Flow", markdown: bool = True, border_style: str = "blue"
    ) -> None:
        """
        Print formatted response.

        Args:
            content: Response content
            source: Source name
            markdown: Whether to render as markdown
            border_style: Panel border color
        """
        if markdown and not content.startswith("["):
            # Render as markdown
            md = Markdown(content)
            panel = Panel(
                md, title=f"[cyan]{source}[/cyan]", border_style=border_style, padding=(1, 2)
            )
        else:
            # Plain text
            panel = Panel(
                content, title=f"[cyan]{source}[/cyan]", border_style=border_style, padding=(1, 2)
            )

        self.console.print(panel)

    def print_error(self, message: str, title: str = "Error") -> None:
        """
        Print error message.

        Args:
            message: Error message
            title: Error title
        """
        panel = Panel(
            f"[red]{message}[/red]",
            title=f"[red bold]{title}[/red bold]",
            border_style="red",
            padding=(1, 2),
        )
        self.console.print(panel)

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[cyan]ℹ[/cyan] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_status(self, status_data: dict[str, Any]) -> None:
        """
        Print system status.

        Args:
            status_data: Status information from /health endpoint
        """
        table = Table(title="[cyan bold]Neura System Status[/cyan bold]", show_header=False)
        table.add_column("Key", style="cyan", width=15)
        table.add_column("Value", style="white")

        # Version & Status
        table.add_row("Version", status_data.get("version", "unknown"))
        table.add_row("Status", f"[green]✓ {status_data.get('status', 'unknown')}[/green]")
        table.add_row("", "")

        # Modules
        table.add_row("[bold]Modules[/bold]", "")
        modules = status_data.get("modules", {})
        for module, state in modules.items():
            icon = "✓" if "loaded" in state else "✗"
            color = "green" if "loaded" in state else "red"
            table.add_row(f"  {module.capitalize()}", f"[{color}]{icon} {state}[/{color}]")

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def print_memory_results(self, results: list[dict[str, Any]]) -> None:
        """
        Print memory search results.

        Args:
            results: List of memory results
        """
        if not results:
            self.print_warning("No memories found")
            return

        panel_content = Text()
        panel_content.append(f"Found {len(results)} result(s)\n\n", style="bold")

        for i, result in enumerate(results, 1):
            entry = result.get("entry", {})
            score = result.get("score", 0)

            panel_content.append(f"{i}. ", style="cyan bold")
            panel_content.append(f"{entry.get('content', '')[:100]}\n", style="white")
            panel_content.append(f"   Score: {score:.3f}", style="dim")
            panel_content.append(
                f" | Created: {entry.get('created_at', 'unknown')}\n\n", style="dim"
            )

        panel = Panel(
            panel_content, title="[cyan]Memory Results[/cyan]", border_style="blue", padding=(1, 2)
        )
        self.console.print(panel)

    def print_why_entries(self, entries: list[dict[str, Any]]) -> None:
        """
        Print WHY Journal entries.

        Args:
            entries: List of WHY entries
        """
        if not entries:
            self.print_warning("No journal entries found")
            return

        table = Table(title=f"[cyan bold]WHY Journal ({len(entries)} entries)[/cyan bold]")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Actor", style="cyan", width=10)
        table.add_column("Action", style="blue", width=20)
        table.add_column("Result", style="white", width=10)

        for entry in entries:
            timestamp = entry.get("timestamp", "")
            if "T" in timestamp:
                time_str = timestamp.split("T")[1][:8]
            else:
                time_str = timestamp[:12]

            result = entry.get("result", "")
            result_color = "green" if result == "SUCCESS" else "red"

            table.add_row(
                time_str,
                entry.get("actor", ""),
                entry.get("action", ""),
                f"[{result_color}]{result}[/{result_color}]",
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()

    def show_progress(self, description: str = "Processing...") -> None:
        """
        Show progress spinner.

        Returns:
            Progress context manager

        Example:
            >>> with ui.show_progress("Thinking..."):
            ...     await cortex.generate(prompt)
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            console=self.console,
            transient=True,
        )


# Global UI instance
_ui = FlowUI()


def get_ui() -> FlowUI:
    """Get global UI instance."""
    return _ui
