"""
Motor Executor - Execute local automation actions safely.

Supports macOS (AppleScript + PyAutoGUI) and Linux (xdotool + PyAutoGUI).
"""

import asyncio
import logging
import os
import platform
import subprocess
import time
import uuid

import pyautogui

from neura.core.types import Result
from neura.core.why_journal import log_action
from neura.motor.types import ActionType, MotorAction, MotorResult, MotorStatus, OSType

logger = logging.getLogger(__name__)

# PyAutoGUI safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner (0,0) to abort
pyautogui.PAUSE = 0.1  # 100ms pause between actions


class MotorExecutor:
    """
    Execute motor actions locally.

    Features:
    - Cross-platform (macOS, Linux)
    - Dry-run mode
    - Confirmation for critical actions
    - WHY Journal logging
    """

    def __init__(self, dry_run: bool = False) -> None:
        """
        Initialize executor.

        Args:
            dry_run: If True, log actions without executing
        """
        self.dry_run = dry_run or os.getenv("MOTOR_DRY_RUN", "").lower() == "true"
        self.pending_confirmations: dict[str, MotorAction] = {}

        if self.dry_run:
            logger.info("Motor running in DRY-RUN mode")

    async def execute(
        self, action: MotorAction, user_approved: bool = False
    ) -> Result[MotorResult]:
        """
        Execute motor action.

        Args:
            action: Action to execute
            user_approved: Whether user has approved (for critical actions)

        Returns:
            Result containing MotorResult
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Log request
            log_action(
                actor="motor",
                action="execute_requested",
                input_summary=f"{action.action.value} on {action.app or 'system'}",
                policy_check="PENDING",
                user_approved=user_approved,
                result="PENDING",
                trace_id=trace_id,
            )

            # Check if critical and not approved
            if action.critical and not user_approved:
                # Store for confirmation
                self.pending_confirmations[trace_id] = action

                log_action(
                    actor="motor",
                    action="confirmation_required",
                    input_summary=f"Critical action: {action.action.value}",
                    policy_check="N/A",
                    user_approved=False,
                    result="PENDING_CONFIRMATION",
                    trace_id=trace_id,
                )

                return Result.success(
                    MotorResult(
                        status=MotorStatus.BLOCKED,
                        reason="Requires user confirmation",
                        duration_ms=0,
                        trace_id=trace_id,
                        action=action,
                    )
                )

            # Dry-run mode
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would execute: {action.model_dump_json()}")

                log_action(
                    actor="motor",
                    action="dry_run_executed",
                    input_summary=f"{action.action.value}",
                    policy_check="PASS",
                    user_approved=user_approved,
                    result="SUCCESS",
                    trace_id=trace_id,
                )

                return Result.success(
                    MotorResult(
                        status=MotorStatus.SUCCESS,
                        reason="Dry-run mode (not actually executed)",
                        duration_ms=0,
                        trace_id=trace_id,
                        action=action,
                    )
                )

            # Detect OS if not specified
            if not action.os:
                action.os = self._detect_os()

            # Execute action based on type
            if action.action == ActionType.OPEN_APP:
                await self._execute_open_app(action)
            elif action.action == ActionType.TYPE_TEXT:
                await self._execute_type_text(action)
            elif action.action == ActionType.CLICK:
                await self._execute_click(action)
            else:
                raise ValueError(f"Unknown action type: {action.action}")

            duration_ms = (time.time() - start_time) * 1000

            # Log success
            log_action(
                actor="motor",
                action="executed",
                input_summary=f"{action.action.value} completed",
                policy_check="PASS",
                user_approved=user_approved,
                result="SUCCESS",
                trace_id=trace_id,
            )

            return Result.success(
                MotorResult(
                    status=MotorStatus.SUCCESS,
                    reason="Action executed successfully",
                    duration_ms=duration_ms,
                    trace_id=trace_id,
                    action=action,
                )
            )

        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)

            # Log failure
            log_action(
                actor="motor",
                action="execution_failed",
                input_summary=f"{action.action.value} failed: {str(e)[:100]}",
                policy_check="N/A",
                user_approved=user_approved,
                result="FAILURE",
                trace_id=trace_id,
            )

            return Result.success(
                MotorResult(
                    status=MotorStatus.FAILURE,
                    reason=f"Execution error: {str(e)}",
                    duration_ms=(time.time() - start_time) * 1000,
                    trace_id=trace_id,
                    action=action,
                )
            )

    async def confirm(self, trace_id: str) -> Result[MotorResult]:
        """
        Confirm and execute a pending critical action.

        Args:
            trace_id: Trace ID of pending action

        Returns:
            Result containing MotorResult
        """
        if trace_id not in self.pending_confirmations:
            return Result.failure("No pending action with this trace_id")

        action = self.pending_confirmations.pop(trace_id)

        # Execute with approval
        return await self.execute(action, user_approved=True)

    def _detect_os(self) -> OSType:
        """Detect current operating system."""
        system = platform.system()

        if system == "Darwin":
            return OSType.MAC
        elif system == "Linux":
            return OSType.LINUX
        else:
            logger.warning(f"Unsupported OS: {system}, defaulting to Linux")
            return OSType.LINUX

    async def _execute_open_app(self, action: MotorAction) -> None:
        """Execute open_app action."""
        if not action.app:
            raise ValueError("app is required for open_app action")

        if action.os == OSType.MAC:
            # macOS: Use AppleScript
            script = f'tell application "{action.app}" to activate'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)

            if result.returncode != 0:
                raise RuntimeError(f"Failed to open {action.app}: {result.stderr.decode()}")

        else:
            # Linux: Try xdg-open first, then wmctrl
            try:
                subprocess.run(
                    ["xdg-open", action.app], capture_output=True, timeout=10, check=True
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Try wmctrl as fallback
                subprocess.run(
                    ["wmctrl", "-a", action.app], capture_output=True, timeout=10, check=True
                )

        # Wait for app to open
        await asyncio.sleep(0.5)

        logger.info(f"Opened app: {action.app}")

    async def _execute_type_text(self, action: MotorAction) -> None:
        """Execute type_text action."""
        if not action.text:
            raise ValueError("text is required for type_text action")

        # Use pyautogui to type
        pyautogui.write(action.text, interval=0.05)

        logger.info(f"Typed {len(action.text)} characters")

    async def _execute_click(self, action: MotorAction) -> None:
        """Execute click action."""
        if action.x is None or action.y is None:
            raise ValueError("x and y coordinates required for click action")

        # Use pyautogui to click
        pyautogui.click(action.x, action.y)

        logger.info(f"Clicked at ({action.x}, {action.y})")


# Singleton
_motor_executor: MotorExecutor | None = None


def get_motor_executor() -> MotorExecutor:
    """Get or create MotorExecutor singleton."""
    global _motor_executor
    if _motor_executor is None:
        _motor_executor = MotorExecutor()
    return _motor_executor
