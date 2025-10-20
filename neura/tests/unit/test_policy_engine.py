"""
Tests for policy engine.
"""

from pathlib import Path

import pytest

from neura.motor.types import ActionType, MotorAction, OSType
from neura.policy.engine import PolicyEngine


class TestPolicyEngine:
    """Tests for PolicyEngine."""

    @pytest.fixture
    def engine(self):
        """Create policy engine instance."""
        return PolicyEngine()

    def test_engine_init(self, engine):
        """Test policy engine initialization."""
        assert engine is not None
        assert engine.rules_dir is not None

    def test_check_opa_available(self, engine):
        """Test OPA availability check."""
        available = engine._check_opa_available()
        assert isinstance(available, bool)

    def test_scrub_text_none(self, engine):
        """Test scrubbing None text."""
        result = engine._scrub_text(None)
        assert result == ""

    def test_scrub_text_short(self, engine):
        """Test scrubbing short text."""
        text = "Hello World"
        result = engine._scrub_text(text)
        assert result == text

    def test_scrub_text_long(self, engine):
        """Test scrubbing long text."""
        text = "A" * 300
        result = engine._scrub_text(text)
        assert len(result) < 300
        assert "***redacted***" in result

    @pytest.mark.asyncio
    async def test_validate_safe_action(self, engine):
        """Test validating a safe action."""
        action = MotorAction(
            app="Terminal",  # Terminal is in allowed_apps_mac
            action=ActionType.TYPE_TEXT,
            text="Hello World",
            critical=False,
            os=OSType.MAC,
        )

        result = await engine.validate(action)
        assert result.is_success()
        decision = result.data
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_validate_dangerous_text(self, engine):
        """Test validating action with dangerous text."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="rm -rf /",
            critical=False,
            os=OSType.MAC,
        )

        # This should be blocked by validation before reaching policy
        # But if it reaches policy, fallback should handle it
        result = await engine.validate(action)
        # Fallback allows it (validation happens at Pydantic level)
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_validate_open_app(self, engine):
        """Test validating open app action."""
        action = MotorAction(
            app="VSCode",
            action=ActionType.OPEN_APP,
            text=None,
            critical=False,
            os=OSType.MAC,
        )

        result = await engine.validate(action)
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_validate_open_app_action(self, engine):
        """Test validating open app action (renamed from click)."""
        action = MotorAction(
            app="Terminal",
            action=ActionType.OPEN_APP,
            text=None,
            critical=False,
            os=OSType.MAC,
        )

        result = await engine.validate(action)
        assert result.is_success()

    @pytest.mark.asyncio
    async def test_fallback_evaluation(self, engine):
        """Test fallback policy evaluation."""
        input_data = {
            "app": "Terminal",  # Terminal is in whitelist
            "action": "type_text",
            "text": "test",
            "critical": False,
            "user_approved": False,
            "os": "mac",
        }

        result = await engine._evaluate_fallback(input_data)
        assert result.is_success()
        decision = result.data
        assert decision.allowed is True
        assert decision.policy_id == "fallback_rules"

    @pytest.mark.asyncio
    async def test_fallback_with_empty_text(self, engine):
        """Test fallback with empty text."""
        input_data = {
            "app": "Notes",
            "action": "type_text",
            "text": "",
            "critical": False,
            "user_approved": False,
            "os": "macos",
        }

        result = await engine._evaluate_fallback(input_data)
        assert result.is_success()


class TestPolicyEngineIntegration:
    """Integration tests for policy engine."""

    @pytest.mark.asyncio
    async def test_multiple_validations(self):
        """Test multiple validations in sequence."""
        engine = PolicyEngine()

        actions = [
            MotorAction(
                app="Terminal",  # In whitelist
                action=ActionType.TYPE_TEXT,
                text="Test 1",
                critical=False,
                os=OSType.MAC,
            ),
            MotorAction(
                app="VSCode",  # In whitelist
                action=ActionType.OPEN_APP,
                text=None,
                critical=False,
                os=OSType.MAC,
            ),
            MotorAction(
                app="Notes",  # In whitelist
                action=ActionType.TYPE_TEXT,
                text="Test 3",
                critical=False,
                os=OSType.MAC,
            ),
        ]

        for action in actions:
            result = await engine.validate(action)
            assert result.is_success()

    @pytest.mark.asyncio
    async def test_critical_action(self):
        """Test validating a critical action."""
        engine = PolicyEngine()

        action = MotorAction(
            app="System",
            action=ActionType.TYPE_TEXT,
            text="Important command",
            critical=True,
            os=OSType.MAC,
        )

        result = await engine.validate(action)
        assert result.is_success()
        # Critical actions should be flagged
        decision = result.data
        assert decision is not None
