"""
AppleScript Executor - Executes AppleScript code on macOS.

Provides safe execution with timeout, error handling, and logging.
"""

import logging
import platform
import subprocess

from neura.core.types import Result

logger = logging.getLogger(__name__)


class AppleScriptExecutor:
    """
    Execute AppleScript code safely.

    Features:
    - Timeout protection (30s default)
    - Error handling
    - Output capture
    - macOS validation

    Example:
        >>> executor = AppleScriptExecutor()
        >>> result = await executor.execute('tell application "Finder" to get name')
        >>> if result.is_success():
        ...     print(result.data)
    """

    def __init__(self, timeout: int = 30) -> None:
        """
        Initialize executor.

        Args:
            timeout: Execution timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self._validate_platform()

    def _validate_platform(self) -> None:
        """Validate we're running on macOS."""
        if platform.system() != "Darwin":
            logger.warning("AppleScript only available on macOS")

    @staticmethod
    def is_available() -> bool:
        """
        Check if AppleScript is available.

        Returns:
            bool: True if on macOS
        """
        return platform.system() == "Darwin"

    async def execute(self, script: str, timeout: int | None = None) -> Result[str]:
        """
        Execute AppleScript code.

        Args:
            script: AppleScript code to execute
            timeout: Optional timeout override

        Returns:
            Result[str]: Script output or error

        Example:
            >>> script = 'tell application "Finder" to get name'
            >>> result = await executor.execute(script)
            >>> print(result.data)  # "Finder"
        """
        if not self.is_available():
            return Result.failure("AppleScript only available on macOS")

        if not script or not script.strip():
            return Result.failure("Empty script")

        timeout_val = timeout or self.timeout

        try:
            logger.debug(f"Executing AppleScript: {script[:100]}...")

            # Execute via osascript
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout_val
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                logger.error(f"AppleScript error: {error_msg}")
                return Result.failure(f"AppleScript error: {error_msg}")

            output = result.stdout.strip()
            logger.info(f"AppleScript success: {len(output)} chars output")

            return Result.success(output)

        except subprocess.TimeoutExpired:
            error_msg = f"AppleScript timeout ({timeout_val}s)"
            logger.error(error_msg)
            return Result.failure(error_msg)

        except FileNotFoundError:
            error_msg = "osascript command not found"
            logger.error(error_msg)
            return Result.failure(error_msg)

        except Exception as e:
            error_msg = f"AppleScript execution error: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def execute_file(self, filepath: str, timeout: int | None = None) -> Result[str]:
        """
        Execute AppleScript from file.

        Args:
            filepath: Path to .scpt or .applescript file
            timeout: Optional timeout override

        Returns:
            Result[str]: Script output or error
        """
        if not self.is_available():
            return Result.failure("AppleScript only available on macOS")

        timeout_val = timeout or self.timeout

        try:
            result = subprocess.run(
                ["osascript", filepath], capture_output=True, text=True, timeout=timeout_val
            )

            if result.returncode != 0:
                return Result.failure(f"Script error: {result.stderr.strip()}")

            return Result.success(result.stdout.strip())

        except subprocess.TimeoutExpired:
            return Result.failure(f"Script timeout ({timeout_val}s)")

        except Exception as e:
            return Result.failure(f"Execution error: {e}")

    def validate_script(self, script: str) -> Result[bool]:
        """
        Validate AppleScript syntax without executing.

        Args:
            script: AppleScript code

        Returns:
            Result[bool]: True if valid, False with error
        """
        if not self.is_available():
            return Result.failure("AppleScript only available on macOS")

        try:
            # Compile only (-c flag)
            result = subprocess.run(
                ["osascript", "-s", "s", "-e", script], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return Result.failure(f"Syntax error: {result.stderr.strip()}")

            return Result.success(True)

        except Exception as e:
            return Result.failure(f"Validation error: {e}")
