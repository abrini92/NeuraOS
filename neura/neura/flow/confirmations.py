"""
Intelligent Confirmations - Smart confirmation flow for critical actions.

Asks for confirmation in natural language for important operations.
"""

import logging
from enum import Enum
from rich.console import Console
from rich.prompt import Confirm

logger = logging.getLogger(__name__)


class ActionRisk(Enum):
    """Risk level of an action."""
    LOW = "low"          # No confirmation needed
    MEDIUM = "medium"    # Ask once
    HIGH = "high"        # Ask with details
    CRITICAL = "critical"  # Ask twice


class ConfirmationManager:
    """
    Manage confirmations for critical actions.
    
    Determines when to ask for confirmation and how to phrase it.
    
    Example:
        >>> manager = ConfirmationManager()
        >>> if await manager.confirm("send_email", {"to": "john@example.com"}):
        ...     send_email()
    """
    
    # Action risk levels
    RISK_LEVELS = {
        # Low risk - no confirmation
        "list_emails": ActionRisk.LOW,
        "list_files": ActionRisk.LOW,
        "get_battery": ActionRisk.LOW,
        "get_volume": ActionRisk.LOW,
        
        # Medium risk - ask once
        "open_folder": ActionRisk.MEDIUM,
        "open_url": ActionRisk.MEDIUM,
        "create_folder": ActionRisk.MEDIUM,
        "create_note": ActionRisk.MEDIUM,
        
        # High risk - ask with details
        "send_email": ActionRisk.HIGH,
        "delete_file": ActionRisk.HIGH,
        "set_volume": ActionRisk.HIGH,
        
        # Critical - ask twice
        "delete_all": ActionRisk.CRITICAL,
        "format_disk": ActionRisk.CRITICAL,
    }
    
    def __init__(self, console: Console | None = None):
        """Initialize confirmation manager."""
        self.console = console or Console()
        logger.info("ConfirmationManager initialized")
    
    async def confirm(
        self,
        action: str,
        parameters: dict | None = None,
        auto_confirm_low: bool = True
    ) -> bool:
        """
        Ask for confirmation if needed.
        
        Args:
            action: Action to confirm
            parameters: Action parameters
            auto_confirm_low: Auto-confirm low-risk actions
            
        Returns:
            bool: Whether action is confirmed
        """
        risk = self.RISK_LEVELS.get(action, ActionRisk.MEDIUM)
        
        # Auto-confirm low risk
        if risk == ActionRisk.LOW and auto_confirm_low:
            return True
        
        # Build confirmation message
        message = self._build_message(action, parameters, risk)
        
        # Ask for confirmation
        if risk == ActionRisk.CRITICAL:
            # Ask twice for critical actions
            self.console.print("[bold red]⚠️ CRITICAL ACTION[/bold red]")
            first = Confirm.ask(message)
            if not first:
                return False
            
            second = Confirm.ask("Are you absolutely sure?")
            return second
        
        elif risk == ActionRisk.HIGH:
            # Show details and ask
            if parameters:
                self.console.print("\n[yellow]Action details:[/yellow]")
                for key, value in parameters.items():
                    self.console.print(f"  • {key}: [bold]{value}[/bold]")
                self.console.print()
            
            return Confirm.ask(message)
        
        elif risk == ActionRisk.MEDIUM:
            # Simple confirmation
            return Confirm.ask(message)
        
        else:
            # Low risk - auto-confirm
            return True
    
    def _build_message(
        self,
        action: str,
        parameters: dict | None,
        risk: ActionRisk
    ) -> str:
        """Build confirmation message."""
        
        # Action-specific messages
        if action == "send_email":
            to = parameters.get("to", "unknown") if parameters else "unknown"
            return f"Send email to {to}?"
        
        elif action == "delete_file":
            file = parameters.get("file", "file") if parameters else "file"
            return f"Delete {file}? This cannot be undone."
        
        elif action == "open_url":
            url = parameters.get("url", "URL") if parameters else "URL"
            return f"Open {url} in browser?"
        
        elif action == "create_folder":
            name = parameters.get("name", "folder") if parameters else "folder"
            return f"Create folder '{name}'?"
        
        elif action == "set_volume":
            level = parameters.get("level", "?") if parameters else "?"
            return f"Set volume to {level}%?"
        
        # Generic message
        return f"Proceed with {action.replace('_', ' ')}?"


# Singleton
_confirmation_manager: ConfirmationManager | None = None


def get_confirmation_manager(console: Console | None = None) -> ConfirmationManager:
    """Get global confirmation manager instance."""
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = ConfirmationManager(console)
    return _confirmation_manager
