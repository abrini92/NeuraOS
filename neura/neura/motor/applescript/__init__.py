"""
AppleScript automation for macOS applications.

Provides complete control over macOS apps via AppleScript.
"""

from neura.motor.applescript.calendar import CalendarScripts
from neura.motor.applescript.executor import AppleScriptExecutor
from neura.motor.applescript.finder import FinderScripts
from neura.motor.applescript.mail import MailScripts
from neura.motor.applescript.notes import NotesScripts
from neura.motor.applescript.safari import SafariScripts
from neura.motor.applescript.system import SystemScripts

__all__ = [
    "AppleScriptExecutor",
    "MailScripts",
    "CalendarScripts",
    "SafariScripts",
    "NotesScripts",
    "FinderScripts",
    "SystemScripts",
]
