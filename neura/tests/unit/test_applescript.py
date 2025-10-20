"""
Unit tests for AppleScript module.

Tests script generation and execution.
"""

import pytest
import platform
from unittest.mock import patch, MagicMock

from neura.motor.applescript.executor import AppleScriptExecutor
from neura.motor.applescript.mail import MailScripts
from neura.motor.applescript.calendar import CalendarScripts
from neura.motor.applescript.safari import SafariScripts
from neura.motor.applescript.notes import NotesScripts
from neura.motor.applescript.finder import FinderScripts
from neura.motor.applescript.system import SystemScripts
from neura.motor.applescript.templates import AppleScriptTemplates


class TestAppleScriptExecutor:
    """Tests for AppleScriptExecutor."""
    
    def test_executor_init(self):
        """Test executor initialization."""
        executor = AppleScriptExecutor(timeout=45)
        assert executor.timeout == 45
    
    def test_is_available_macos(self):
        """Test availability check on macOS."""
        with patch('platform.system', return_value='Darwin'):
            assert AppleScriptExecutor.is_available() is True
    
    def test_is_available_not_macos(self):
        """Test availability check on non-macOS."""
        with patch('platform.system', return_value='Linux'):
            assert AppleScriptExecutor.is_available() is False
    
    @pytest.mark.asyncio
    async def test_execute_empty_script(self):
        """Test execution with empty script."""
        executor = AppleScriptExecutor()
        result = await executor.execute("")
        
        assert result.is_failure()
        assert "Empty script" in result.error
    
    @pytest.mark.asyncio
    @patch('platform.system', return_value='Linux')
    async def test_execute_on_non_macos(self, mock_platform):
        """Test execution fails gracefully on non-macOS."""
        executor = AppleScriptExecutor()
        result = await executor.execute('tell application "Finder" to get name')
        
        assert result.is_failure()
        assert "only available on macOS" in result.error
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS only")
    async def test_execute_simple_script(self):
        """Test executing simple script on macOS."""
        executor = AppleScriptExecutor()
        result = await executor.execute('return "Hello"')
        
        if result.is_success():
            assert result.data == "Hello"


class TestMailScripts:
    """Tests for Mail script generation."""
    
    def test_list_inbox_generation(self):
        """Test inbox list script generation."""
        script = MailScripts.list_inbox(limit=5)
        
        assert 'tell application "Mail"' in script
        assert 'messages of inbox' in script
        assert '5' in script
    
    def test_read_email_generation(self):
        """Test read email script generation."""
        script = MailScripts.read_email(index=3)
        
        assert 'tell application "Mail"' in script
        assert 'message 3' in script
        assert 'content of msg' in script
    
    def test_search_emails_generation(self):
        """Test search script generation."""
        script = MailScripts.search_emails("project")
        
        assert 'tell application "Mail"' in script
        assert 'project' in script
        assert 'subject contains' in script
    
    def test_send_email_generation(self):
        """Test send email script generation."""
        script = MailScripts.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert 'tell application "Mail"' in script
        assert 'test@example.com' in script
        assert 'Test Subject' in script
        assert 'send' in script
    
    def test_send_email_escaping(self):
        """Test special character escaping in email."""
        script = MailScripts.send_email(
            to='user@example.com',
            subject='Test "quoted" subject',
            body='Body with "quotes"'
        )
        
        # Quotes should be escaped
        assert '\\"' in script


class TestCalendarScripts:
    """Tests for Calendar script generation."""
    
    def test_list_today_events(self):
        """Test today's events script."""
        script = CalendarScripts.list_today_events()
        
        assert 'tell application "Calendar"' in script
        assert 'current date' in script
        assert 'every event' in script
    
    def test_create_event_generation(self):
        """Test event creation script."""
        script = CalendarScripts.create_event(
            title="Meeting",
            start_date="today",
            start_time="10:00 AM"
        )
        
        assert 'tell application "Calendar"' in script
        assert 'Meeting' in script
        assert 'make new event' in script
    
    def test_search_events_generation(self):
        """Test event search script."""
        script = CalendarScripts.search_events("meeting")
        
        assert 'tell application "Calendar"' in script
        assert 'meeting' in script
        assert 'summary contains' in script


class TestSafariScripts:
    """Tests for Safari script generation."""
    
    def test_open_url_generation(self):
        """Test URL opening script."""
        script = SafariScripts.open_url("https://example.com")
        
        assert 'tell application "Safari"' in script
        assert 'https://example.com' in script
    
    def test_search_google_generation(self):
        """Test Google search script."""
        script = SafariScripts.search_google("python tutorial")
        
        assert 'tell application "Safari"' in script
        assert 'google.com/search' in script
        assert 'python' in script
    
    def test_execute_javascript_generation(self):
        """Test JavaScript execution script."""
        script = SafariScripts.execute_javascript("document.title")
        
        assert 'tell application "Safari"' in script
        assert 'do JavaScript' in script
        assert 'document.title' in script


class TestNotesScripts:
    """Tests for Notes script generation."""
    
    def test_create_note_generation(self):
        """Test note creation script."""
        script = NotesScripts.create_note("Test Note", "Note body")
        
        assert 'tell application "Notes"' in script
        assert 'Test Note' in script
        assert 'Note body' in script
        assert 'make new note' in script
    
    def test_list_notes_generation(self):
        """Test notes listing script."""
        script = NotesScripts.list_notes(limit=5)
        
        assert 'tell application "Notes"' in script
        assert '5' in script
    
    def test_search_notes_generation(self):
        """Test notes search script."""
        script = NotesScripts.search_notes("todo")
        
        assert 'tell application "Notes"' in script
        assert 'todo' in script
        assert 'contains' in script


class TestFinderScripts:
    """Tests for Finder script generation."""
    
    def test_list_files_generation(self):
        """Test file listing script."""
        script = FinderScripts.list_files(folder="Desktop")
        
        assert 'tell application "Finder"' in script
        assert 'Desktop' in script
        assert 'items of theFolder' in script
    
    def test_search_files_generation(self):
        """Test file search script."""
        script = FinderScripts.search_files("document")
        
        assert 'tell application "Finder"' in script
        assert 'document' in script
        assert 'name contains' in script
    
    def test_get_disk_space_generation(self):
        """Test disk space script."""
        script = FinderScripts.get_disk_space()
        
        assert 'tell application "Finder"' in script
        assert 'capacity' in script
        assert 'free space' in script


class TestSystemScripts:
    """Tests for System script generation."""
    
    def test_get_volume_generation(self):
        """Test volume get script."""
        script = SystemScripts.get_volume()
        
        assert 'get volume settings' in script
        assert 'output volume' in script
    
    def test_set_volume_generation(self):
        """Test volume set script."""
        script = SystemScripts.set_volume(50)
        
        assert 'set volume' in script
        assert '50' in script
    
    def test_set_volume_clamping(self):
        """Test volume level clamping."""
        # Too high
        script = SystemScripts.set_volume(150)
        assert '100' in script
        
        # Too low
        script = SystemScripts.set_volume(-10)
        assert '0' in script
    
    def test_get_battery_generation(self):
        """Test battery status script."""
        script = SystemScripts.get_battery()
        
        assert 'pmset -g batt' in script
    
    def test_take_screenshot_generation(self):
        """Test screenshot script."""
        script = SystemScripts.take_screenshot("/tmp/test.png")
        
        assert 'screencapture' in script
        assert '/tmp/test.png' in script


class TestAppleScriptTemplates:
    """Tests for generic templates."""
    
    def test_tell_app_generation(self):
        """Test tell application template."""
        script = AppleScriptTemplates.tell_app("Finder", "get name")
        
        assert 'tell application "Finder"' in script
        assert 'get name' in script
        assert 'end tell' in script
    
    def test_activate_app_generation(self):
        """Test app activation."""
        script = AppleScriptTemplates.activate_app("Safari")
        
        assert 'tell application "Safari"' in script
        assert 'activate' in script
    
    def test_keystroke_no_modifiers(self):
        """Test keystroke without modifiers."""
        script = AppleScriptTemplates.keystroke("a")
        
        assert 'keystroke "a"' in script
        assert 'System Events' in script
    
    def test_keystroke_with_modifiers(self):
        """Test keystroke with modifiers."""
        script = AppleScriptTemplates.keystroke("c", modifiers=["command"])
        
        assert 'keystroke "c"' in script
        assert 'command down' in script


@pytest.mark.integration
@pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS only")
class TestAppleScriptIntegration:
    """Integration tests on real macOS."""
    
    @pytest.mark.asyncio
    async def test_simple_command_execution(self):
        """Test executing simple AppleScript."""
        executor = AppleScriptExecutor()
        result = await executor.execute('return "test"')
        
        assert result.is_success()
        assert result.data == "test"
    
    @pytest.mark.asyncio
    async def test_get_date_execution(self):
        """Test getting system date."""
        executor = AppleScriptExecutor()
        script = SystemScripts.get_date_time()
        result = await executor.execute(script)
        
        assert result.is_success()
        assert len(result.data) > 0
    
    @pytest.mark.asyncio
    async def test_list_running_apps(self):
        """Test listing running applications."""
        executor = AppleScriptExecutor()
        script = AppleScriptTemplates.list_running_apps()
        result = await executor.execute(script)
        
        assert result.is_success()
        assert "Finder" in result.data  # Finder is always running
