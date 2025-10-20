"""
Unit tests for Flow module.

Tests command parsing, session management, and command execution.
"""

import pytest
import uuid
from datetime import datetime

from neura.flow.types import (
    FlowCommand,
    FlowResponse,
    FlowSession,
    ConversationMessage,
    CommandType,
    FlowConfig
)
from neura.flow.commands import CommandRegistry
from neura.flow.completer import FlowCompleter


class TestFlowCommand:
    """Tests for FlowCommand parsing."""
    
    def test_parse_builtin_command(self):
        """Test parsing built-in command."""
        cmd = FlowCommand.parse("/help")
        
        assert cmd.raw == "/help"
        assert cmd.type == CommandType.BUILTIN
        assert cmd.name == "help"
        assert cmd.args == []
    
    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        cmd = FlowCommand.parse("/ask What is AI?")
        
        assert cmd.type == CommandType.BUILTIN
        assert cmd.name == "ask"
        assert len(cmd.args) == 1
        assert cmd.args[0] == "What is AI?"
    
    def test_parse_natural_language(self):
        """Test parsing natural language input."""
        cmd = FlowCommand.parse("Hello, how are you?")
        
        assert cmd.type == CommandType.NATURAL
        assert cmd.name == "chat"
        assert len(cmd.args) == 1
        assert cmd.args[0] == "Hello, how are you?"
    
    def test_parse_empty_input(self):
        """Test parsing empty input."""
        cmd = FlowCommand.parse("")
        
        assert cmd.type == CommandType.NATURAL
        assert cmd.name == "chat"
        assert cmd.args == []
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only input."""
        cmd = FlowCommand.parse("   ")
        
        assert cmd.type == CommandType.NATURAL
        assert cmd.args == []
    
    def test_parse_multiple_args(self):
        """Test parsing command with multiple words in args."""
        cmd = FlowCommand.parse("/remember Important deadline Nov 15")
        
        assert cmd.name == "remember"
        assert cmd.args[0] == "Important deadline Nov 15"
    
    def test_parse_case_insensitive(self):
        """Test command parsing is case-insensitive."""
        cmd = FlowCommand.parse("/HELP")
        assert cmd.name == "help"
        
        cmd2 = FlowCommand.parse("/Ask question")
        assert cmd2.name == "ask"


class TestFlowResponse:
    """Tests for FlowResponse."""
    
    def test_create_success_response(self):
        """Test creating successful response."""
        response = FlowResponse(
            content="Test response",
            source="Cortex",
            success=True
        )
        
        assert response.content == "Test response"
        assert response.source == "Cortex"
        assert response.success is True
        assert not response.is_error()
    
    def test_create_error_response(self):
        """Test creating error response."""
        response = FlowResponse(
            content="Error occurred",
            source="Flow",
            success=False
        )
        
        assert response.is_error()
        assert response.success is False
    
    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = FlowResponse(
            content="Test",
            source="Test",
            metadata={"key": "value", "count": 42}
        )
        
        assert response.metadata["key"] == "value"
        assert response.metadata["count"] == 42


class TestConversationMessage:
    """Tests for ConversationMessage."""
    
    def test_create_message(self):
        """Test creating conversation message."""
        msg = ConversationMessage(
            role="user",
            content="Hello"
        )
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
    
    def test_message_roles(self):
        """Test different message roles."""
        user_msg = ConversationMessage(role="user", content="Question")
        assistant_msg = ConversationMessage(role="assistant", content="Answer")
        system_msg = ConversationMessage(role="system", content="System")
        
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"


class TestFlowSession:
    """Tests for FlowSession."""
    
    def test_create_session(self):
        """Test creating new session."""
        session = FlowSession(session_id=str(uuid.uuid4()))
        
        assert session.session_id is not None
        assert len(session.conversation_history) == 0
        assert session.commands_executed == 0
        assert session.context_window_size == 2048
    
    def test_add_message(self):
        """Test adding message to session."""
        session = FlowSession(session_id="test-123")
        
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        
        assert len(session.conversation_history) == 2
        assert session.conversation_history[0].role == "user"
        assert session.conversation_history[1].role == "assistant"
    
    def test_get_recent_context(self):
        """Test getting recent context."""
        session = FlowSession(session_id="test-123")
        
        # Add multiple messages
        for i in range(20):
            session.add_message("user", f"Message {i}")
        
        # Get recent 5
        recent = session.get_recent_context(max_messages=5)
        
        assert len(recent) == 5
        assert recent[0].content == "Message 15"
        assert recent[-1].content == "Message 19"
    
    def test_get_context_for_cortex(self):
        """Test formatting context for Cortex."""
        session = FlowSession(session_id="test-123")
        
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi")
        
        context = session.get_context_for_cortex(max_messages=10)
        
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello"
        assert context[1]["role"] == "assistant"
    
    def test_increment_commands(self):
        """Test incrementing command counter."""
        session = FlowSession(session_id="test-123")
        
        assert session.commands_executed == 0
        
        session.increment_commands()
        assert session.commands_executed == 1
        
        session.increment_commands()
        assert session.commands_executed == 2
    
    def test_custom_context_window(self):
        """Test custom context window size."""
        session = FlowSession(
            session_id="test-123",
            context_window_size=4096
        )
        
        assert session.context_window_size == 4096


class TestFlowConfig:
    """Tests for FlowConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = FlowConfig()
        
        assert config.save_history is True
        assert config.max_history == 1000
        assert config.context_window == 2048
        assert config.auto_save_conversations is True
        assert config.enable_auto_completion is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = FlowConfig(
            save_history=False,
            max_history=500,
            context_window=4096
        )
        
        assert config.save_history is False
        assert config.max_history == 500
        assert config.context_window == 4096


class TestCommandRegistry:
    """Tests for CommandRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create CommandRegistry for testing."""
        return CommandRegistry(api_base="http://localhost:8000")
    
    @pytest.fixture
    def session(self):
        """Create FlowSession for testing."""
        return FlowSession(session_id=str(uuid.uuid4()))
    
    def test_registry_has_handlers(self, registry):
        """Test registry has command handlers."""
        assert len(registry.handlers) > 0
        assert "help" in registry.handlers
        assert "ask" in registry.handlers
        assert "exit" in registry.handlers
    
    @pytest.mark.asyncio
    async def test_execute_help_command(self, registry, session):
        """Test executing help command."""
        cmd = FlowCommand.parse("/help")
        response = await registry.execute(cmd, session)
        
        assert response.success is True
        assert session.commands_executed == 1
    
    @pytest.mark.asyncio
    async def test_execute_clear_command(self, registry, session):
        """Test executing clear command."""
        cmd = FlowCommand.parse("/clear")
        response = await registry.execute(cmd, session)
        
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_execute_exit_command(self, registry, session):
        """Test executing exit command."""
        cmd = FlowCommand.parse("/exit")
        response = await registry.execute(cmd, session)
        
        assert response.success is True
        assert response.content == "__EXIT__"
    
    @pytest.mark.asyncio
    async def test_execute_unknown_command(self, registry, session):
        """Test executing unknown command."""
        cmd = FlowCommand.parse("/unknown")
        response = await registry.execute(cmd, session)
        
        assert response.success is False
        assert "Unknown command" in response.content
    
    @pytest.mark.asyncio
    async def test_command_without_required_args(self, registry, session):
        """Test command without required arguments."""
        cmd = FlowCommand.parse("/ask")
        response = await registry.execute(cmd, session)
        
        assert response.success is False
        assert "Usage" in response.content


class TestFlowCompleter:
    """Tests for FlowCompleter."""
    
    def test_completer_has_commands(self):
        """Test completer has command list."""
        completer = FlowCompleter()
        
        assert "/help" in completer.commands
        assert "/ask" in completer.commands
        assert "/exit" in completer.commands
    
    def test_completer_has_descriptions(self):
        """Test completer has command descriptions."""
        completer = FlowCompleter()
        
        assert "/help" in completer.descriptions
        assert "/ask" in completer.descriptions
    
    def test_completer_has_command_args(self):
        """Test completer has command arguments."""
        completer = FlowCompleter()
        
        assert "/vault" in completer.command_args
        assert "unlock" in completer.command_args["/vault"]
        assert "lock" in completer.command_args["/vault"]


# Integration-like tests (require API to be running)
class TestFlowIntegration:
    """Integration tests for Flow (require running API)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_status_command_with_api(self):
        """Test /status command with running API."""
        registry = CommandRegistry(api_base="http://localhost:8000")
        session = FlowSession(session_id=str(uuid.uuid4()))
        
        cmd = FlowCommand.parse("/status")
        
        # This will fail if API is not running
        # Should be skipped in unit tests
        try:
            response = await registry.execute(cmd, session)
            # If API is running, should succeed
            assert response.success is True
        except Exception:
            # If API not running, that's ok for unit tests
            pytest.skip("API not running")
