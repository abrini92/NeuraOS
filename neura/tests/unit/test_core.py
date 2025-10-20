"""
Unit tests for core module.
"""

import pytest
from neura.core.exceptions import CoreError, NeuraError
from neura.core.types import Event, Result, ResultStatus


class TestResult:
    """Test Result type."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = Result.success({"key": "value"})
        assert result.is_success()
        assert not result.is_failure()
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test creating a failed result."""
        result = Result.failure("Something went wrong")
        assert result.is_failure()
        assert not result.is_success()
        assert result.error == "Something went wrong"
        assert result.data is None

    def test_unwrap_success(self) -> None:
        """Test unwrapping a successful result."""
        result = Result.success(42)
        assert result.unwrap() == 42

    def test_unwrap_failure(self) -> None:
        """Test unwrapping a failed result raises."""
        result: Result[int] = Result.failure("Error")
        with pytest.raises(ValueError, match="Cannot unwrap failed result"):
            result.unwrap()


class TestEvent:
    """Test Event type."""

    def test_create_event(self) -> None:
        """Test creating an event."""
        event = Event.create(
            name="test.event",
            data={"message": "Hello"},
            source="test_module",
        )
        assert event.name == "test.event"
        assert event.data == {"message": "Hello"}
        assert event.source == "test_module"
        assert event.timestamp is not None


class TestExceptions:
    """Test exception hierarchy."""

    def test_neura_error(self) -> None:
        """Test NeuraError base exception."""
        error = NeuraError("Test error", details={"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert "Test error" in str(error)

    def test_core_error(self) -> None:
        """Test CoreError inherits from NeuraError."""
        error = CoreError("Core error")
        assert isinstance(error, NeuraError)
        assert error.message == "Core error"
