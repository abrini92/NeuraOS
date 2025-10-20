"""
AppleScript Flow Commands - Execute AppleScript operations from Flow.

Integrates AppleScript automation into Flow REPL.
"""

import logging

from neura.core.types import Result
from neura.motor.applescript import (
    AppleScriptExecutor,
    FinderScripts,
    NotesScripts,
    SafariScripts,
    SystemScripts,
)

logger = logging.getLogger(__name__)


class AppleScriptFlowHandler:
    """Handler for AppleScript commands in Flow."""

    def __init__(self) -> None:
        """Initialize AppleScript handler."""
        self.executor = AppleScriptExecutor()

    async def execute(self, category: str, operation: str, args: str = "") -> Result[str]:
        """
        Execute AppleScript command.

        Args:
            category: App category (finder, system, safari, notes)
            operation: Operation to perform
            args: Additional arguments

        Returns:
            Result[str]: Command output or error
        """
        if not self.executor.is_available():
            return Result.failure("AppleScript only available on macOS")

        try:
            # Route to appropriate handler
            if category == "finder":
                return await self._handle_finder(operation, args)
            elif category == "system":
                return await self._handle_system(operation, args)
            elif category == "safari":
                return await self._handle_safari(operation, args)
            elif category == "notes":
                return await self._handle_notes(operation, args)
            else:
                return Result.failure(f"Unknown AppleScript category: {category}")

        except Exception as e:
            logger.error(f"AppleScript error: {e}")
            return Result.failure(f"AppleScript error: {e}")

    async def _handle_finder(self, operation: str, args: str) -> Result[str]:
        """Handle Finder operations with contextual responses."""
        from neura.core.personality import get_personality
        personality = get_personality()
        
        if operation == "list":
            # Default to Desktop
            folder = args.strip() if args.strip() else "Desktop"
            script = FinderScripts.list_files(folder=folder, max_items=10)
            result = await self.executor.execute(script)
            
            if result.is_success():
                # Add contextual message
                files = result.data.split('\n')
                count = len([f for f in files if f.strip()])
                return Result.success(f"Found {count} items in {folder}:\n{result.data}")
            return result
        
        elif operation == "open":
            folder = args.strip() if args.strip() else "Desktop"
            script = FinderScripts.open_folder(folder)
            result = await self.executor.execute(script)
            
            if result.is_success():
                return Result.success(f"{personality.get_response('success')}. Opened {folder}")
            return result
        
        elif operation == "disk":
            script = FinderScripts.get_disk_space()
            result = await self.executor.execute(script)
            
            if result.is_success():
                return Result.success(f"Disk space: {result.data}")
            return result
        
        elif operation == "create":
            if not args.strip():
                return Result.failure("Folder name required")
            script = FinderScripts.create_folder(args.strip(), location="Desktop")
            result = await self.executor.execute(script)
            
            if result.is_success():
                return Result.success(f"{personality.get_response('success')}. Created folder '{args.strip()}'")
            return result
        
        else:
            return Result.failure(f"Unknown Finder operation: {operation}")

    async def _handle_system(self, operation: str, args: str) -> Result[str]:
        """Handle System operations."""
        if operation == "volume":
            if args.strip():
                # Set volume
                try:
                    level = int(args.strip())
                    script = SystemScripts.set_volume(level)
                    return await self.executor.execute(script)
                except ValueError:
                    return Result.failure("Volume must be a number (0-100)")
            else:
                # Get volume
                script = SystemScripts.get_volume()
                return await self.executor.execute(script)

        elif operation == "battery":
            script = SystemScripts.get_battery()
            return await self.executor.execute(script)

        elif operation == "screenshot":
            filepath = args.strip() if args.strip() else "~/Desktop/screenshot.png"
            script = SystemScripts.take_screenshot(filepath)
            return await self.executor.execute(script)

        elif operation == "clipboard":
            script = SystemScripts.get_clipboard()
            return await self.executor.execute(script)

        else:
            return Result.failure(f"Unknown System operation: {operation}")

    async def _handle_safari(self, operation: str, args: str) -> Result[str]:
        """Handle Safari operations."""
        if operation == "open":
            if not args.strip():
                return Result.failure("URL required")
            script = SafariScripts.open_url(args.strip())
            return await self.executor.execute(script)

        elif operation == "google":
            if not args.strip():
                return Result.failure("Search query required")
            script = SafariScripts.search_google(args.strip())
            return await self.executor.execute(script)

        else:
            return Result.failure(f"Unknown Safari operation: {operation}")

    async def _handle_notes(self, operation: str, args: str) -> Result[str]:
        """Handle Notes operations."""
        if operation == "list":
            script = NotesScripts.list_notes(limit=10)
            return await self.executor.execute(script)

        elif operation == "create":
            if not args.strip():
                return Result.failure("Note title required")
            # Extract title and body if provided
            parts = args.strip().split(":", 1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""
            script = NotesScripts.create_note(title, body)
            return await self.executor.execute(script)

        else:
            return Result.failure(f"Unknown Notes operation: {operation}")
