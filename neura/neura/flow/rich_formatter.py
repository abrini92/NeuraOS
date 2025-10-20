"""
Rich Formatter - Beautiful visual feedback with Rich library.

Formats outputs with panels, tables, and colors.
"""

import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown

logger = logging.getLogger(__name__)


class RichFormatter:
    """
    Format outputs beautifully with Rich.
    
    Provides methods to format different types of content:
    - Email lists
    - File lists
    - Calendar events
    - Code snippets
    - Error messages
    
    Example:
        >>> formatter = RichFormatter()
        >>> formatter.format_emails(emails)
    """
    
    def __init__(self, console: Console | None = None):
        """Initialize formatter."""
        self.console = console or Console()
        logger.info("RichFormatter initialized")
    
    def format_emails(self, emails: list[dict]) -> Panel:
        """
        Format email list as a beautiful panel.
        
        Args:
            emails: List of email dicts with from, subject, preview
            
        Returns:
            Panel: Formatted email panel
        """
        if not emails:
            return Panel(
                "[dim]No emails found[/dim]",
                title="📧 Inbox",
                border_style="blue"
            )
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("№", style="cyan", width=3)
        table.add_column("From", style="bold", width=20)
        table.add_column("Subject", style="white")
        
        for i, email in enumerate(emails[:10], 1):
            from_name = email.get("from", "Unknown")[:20]
            subject = email.get("subject", "No subject")[:40]
            
            table.add_row(
                str(i),
                from_name,
                subject
            )
        
        count_text = f"{len(emails)} email{'s' if len(emails) > 1 else ''}"
        
        return Panel(
            table,
            title=f"📧 Your Inbox ({count_text})",
            border_style="blue",
            padding=(1, 2)
        )
    
    def format_files(self, files: list[str], folder: str = "Desktop") -> Panel:
        """
        Format file list as a panel.
        
        Args:
            files: List of file names
            folder: Folder name
            
        Returns:
            Panel: Formatted file panel
        """
        if not files:
            return Panel(
                "[dim]No files found[/dim]",
                title=f"📁 {folder}",
                border_style="green"
            )
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Icon", width=3)
        table.add_column("Name", style="white")
        
        for file in files[:20]:
            # Determine icon
            if file.endswith("/"):
                icon = "📁"
                name = file[:-1]
            elif any(file.endswith(ext) for ext in [".py", ".js", ".ts"]):
                icon = "📄"
                name = file
            elif any(file.endswith(ext) for ext in [".jpg", ".png", ".gif"]):
                icon = "🖼️"
                name = file
            elif any(file.endswith(ext) for ext in [".pdf", ".doc"]):
                icon = "📝"
                name = file
            else:
                icon = "📄"
                name = file
            
            table.add_row(icon, name)
        
        count = len(files)
        return Panel(
            table,
            title=f"📁 {folder} ({count} items)",
            border_style="green",
            padding=(1, 2)
        )
    
    def format_calendar(self, events: list[dict]) -> Panel:
        """
        Format calendar events as a panel.
        
        Args:
            events: List of event dicts with title, time, location
            
        Returns:
            Panel: Formatted calendar panel
        """
        if not events:
            return Panel(
                "[dim]No upcoming events[/dim]",
                title="📅 Calendar",
                border_style="cyan"
            )
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Event", style="bold")
        table.add_column("Location", style="dim")
        
        for event in events[:10]:
            time = event.get("time", "TBD")
            title = event.get("title", "Untitled")
            location = event.get("location", "")
            
            table.add_row(time, title, location)
        
        return Panel(
            table,
            title="📅 Your Calendar",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def format_code(self, code: str, language: str = "python") -> Syntax:
        """
        Format code with syntax highlighting.
        
        Args:
            code: Code string
            language: Programming language
            
        Returns:
            Syntax: Formatted code
        """
        return Syntax(code, language, theme="monokai", line_numbers=True)
    
    def format_error(self, error: str, suggestion: str | None = None) -> Panel:
        """
        Format error message empathetically.
        
        Args:
            error: Error message
            suggestion: Optional suggestion
            
        Returns:
            Panel: Formatted error panel
        """
        content = f"[red]{error}[/red]"
        
        if suggestion:
            content += f"\n\n[yellow]💡 Suggestion:[/yellow]\n{suggestion}"
        
        return Panel(
            content,
            title="⚠️ Hmm, something's off",
            border_style="red",
            padding=(1, 2)
        )
    
    def format_success(self, message: str, details: str | None = None) -> Panel:
        """
        Format success message.
        
        Args:
            message: Success message
            details: Optional details
            
        Returns:
            Panel: Formatted success panel
        """
        content = f"[green]{message}[/green]"
        
        if details:
            content += f"\n\n[dim]{details}[/dim]"
        
        return Panel(
            content,
            title="✓ Done",
            border_style="green",
            padding=(1, 2)
        )
    
    def format_thinking(self, task: str) -> str:
        """
        Format thinking/processing message.
        
        Args:
            task: Task description
            
        Returns:
            str: Formatted message
        """
        return f"[dim]🤔 {task}...[/dim]"
    
    def format_markdown(self, text: str) -> Markdown:
        """
        Format markdown text.
        
        Args:
            text: Markdown text
            
        Returns:
            Markdown: Formatted markdown
        """
        return Markdown(text)


# Singleton
_rich_formatter: RichFormatter | None = None


def get_rich_formatter(console: Console | None = None) -> RichFormatter:
    """Get global rich formatter instance."""
    global _rich_formatter
    if _rich_formatter is None:
        _rich_formatter = RichFormatter(console)
    return _rich_formatter
