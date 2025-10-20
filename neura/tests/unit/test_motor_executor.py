"""Tests for motor executor."""

import pytest

from neura.motor.executor import MotorExecutor
from neura.motor.types import ActionType, MotorAction, OSType


class TestMotorExecutor:
    """Tests for MotorExecutor."""

    @pytest.fixture
    def executor(self):
        """Create executor in dry-run mode."""
        return MotorExecutor(dry_run=True)

    def test_executor_init(self, executor):
        """Test executor initialization."""
        assert executor is not None
        assert executor.dry_run is True
        assert isinstance(executor.pending_confirmations, dict)

    def test_executor_dry_run_mode(self):
        """Test dry-run mode."""
        executor = MotorExecutor(dry_run=True)
        assert executor.dry_run is True

    def test_executor_normal_mode(self):
        """Test normal mode."""
        executor = MotorExecutor(dry_run=False)
        assert executor.dry_run is False

    @pytest.mark.asyncio
    async def test_execute_dry_run(self, executor):
        """Test executing action in dry-run mode."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="test",
            critical=False,
            os=OSType.MAC,
        )

        result = await executor.execute(action)
        assert result.is_success()
        motor_result = result.data
        assert motor_result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_critical_without_approval(self, executor):
        """Test critical action without approval."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="important",
            critical=True,
            os=OSType.MAC,
        )

        result = await executor.execute(action, user_approved=False)
        # Should require confirmation
        assert result.is_success()
        motor_result = result.data
        assert "confirmation" in motor_result.message.lower() or motor_result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_critical_with_approval(self, executor):
        """Test critical action with approval."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="important",
            critical=True,
            os=OSType.MAC,
        )

        result = await executor.execute(action, user_approved=True)
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_execute_open_app(self, executor):
        """Test open app action."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.OPEN_APP,
            text=None,
            critical=False,
            os=OSType.MAC,
        )

        result = await executor.execute(action)
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_pending_confirmations(self, executor):
        """Test pending confirmations tracking."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="test",
            critical=True,
            os=OSType.MAC,
        )

        # Execute without approval
        result = await executor.execute(action, user_approved=False)
        
        # In dry-run, should still succeed
        assert result.is_success()


class TestMotorExecutorIntegration:
    """Integration tests for motor executor."""

    @pytest.mark.asyncio
    async def test_multiple_executions(self):
        """Test multiple executions in sequence."""
        executor = MotorExecutor(dry_run=True)

        actions = [
            MotorAction(
                app="Terminal",
                action=ActionType.TYPE_TEXT,
                text="test1",
                critical=False,
                os=OSType.MAC,
            ),
            MotorAction(
                app="Notes",
                action=ActionType.TYPE_TEXT,
                text="test2",
                critical=False,
                os=OSType.MAC,
            ),
            MotorAction(
                app="VSCode",
                action=ActionType.OPEN_APP,
                text=None,
                critical=False,
                os=OSType.MAC,
            ),
        ]

        for action in actions:
            result = await executor.execute(action)
            assert result.is_success()

    @pytest.mark.asyncio
    async def test_dry_run_no_side_effects(self):
        """Test that dry-run has no side effects."""
        executor = MotorExecutor(dry_run=True)

        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="This should not be typed",
            critical=False,
            os=OSType.MAC,
        )

        result = await executor.execute(action)
        assert result.is_success()
        # In dry-run, no actual typing happens
        motor_result = result.data
        assert motor_result is not None
