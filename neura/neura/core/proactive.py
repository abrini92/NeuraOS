"""
Proactive Suggestions Engine - Anticipate user needs.

Monitors context and makes intelligent suggestions.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from neura.core.context import get_context_engine, Context, UserMood, TimeOfDay
from neura.core.personality import get_personality

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A proactive suggestion."""
    type: str
    message: str
    action: str | None
    priority: int  # 1-5, 5 being highest
    timestamp: datetime


class ProactiveEngine:
    """
    Engine for making proactive suggestions.
    
    Monitors context and suggests actions before being asked.
    
    Example:
        >>> engine = ProactiveEngine()
        >>> suggestions = await engine.get_suggestions()
        >>> for suggestion in suggestions:
        ...     print(suggestion.message)
    """
    
    def __init__(self):
        """Initialize proactive engine."""
        self.context_engine = get_context_engine()
        self.personality = get_personality()
        self._last_battery_warning: datetime | None = None
        self._last_break_suggestion: datetime | None = None
        logger.info("ProactiveEngine initialized")
    
    async def get_suggestions(self) -> list[Suggestion]:
        """
        Get current proactive suggestions.
        
        Returns:
            list[Suggestion]: List of suggestions
        """
        context = await self.context_engine.get_context()
        suggestions = []
        
        # Battery warning
        battery_suggestion = await self._check_battery(context)
        if battery_suggestion:
            suggestions.append(battery_suggestion)
        
        # Break suggestion
        break_suggestion = await self._check_break_needed(context)
        if break_suggestion:
            suggestions.append(break_suggestion)
        
        # Morning briefing
        briefing_suggestion = await self._check_morning_briefing(context)
        if briefing_suggestion:
            suggestions.append(briefing_suggestion)
        
        # Calendar reminder
        calendar_suggestion = await self._check_calendar(context)
        if calendar_suggestion:
            suggestions.append(calendar_suggestion)
        
        # Sort by priority
        suggestions.sort(key=lambda s: s.priority, reverse=True)
        
        return suggestions
    
    async def _check_battery(self, context: Context) -> Suggestion | None:
        """Check if battery warning needed."""
        # Don't spam warnings
        if self._last_battery_warning:
            if datetime.now() - self._last_battery_warning < timedelta(minutes=30):
                return None
        
        battery = context.system.battery_level
        charging = context.system.battery_charging
        
        if battery < 20 and not charging:
            self._last_battery_warning = datetime.now()
            
            message = f"Battery is low at {battery}%. Want me to close unused apps?"
            
            return Suggestion(
                type="battery_low",
                message=message,
                action="close_apps",
                priority=5,
                timestamp=datetime.now()
            )
        
        elif battery < 10 and not charging:
            message = f"⚠️ Battery critical at {battery}%! Please charge soon."
            
            return Suggestion(
                type="battery_critical",
                message=message,
                action=None,
                priority=5,
                timestamp=datetime.now()
            )
        
        return None
    
    async def _check_break_needed(self, context: Context) -> Suggestion | None:
        """Check if user needs a break."""
        # Don't spam break suggestions
        if self._last_break_suggestion:
            if datetime.now() - self._last_break_suggestion < timedelta(hours=1):
                return None
        
        # Suggest break if busy during work hours
        if (context.user.inferred_mood == UserMood.BUSY and
            context.temporal.is_work_hours and
            len(context.user.recent_commands) > 10):
            
            self._last_break_suggestion = datetime.now()
            
            message = "You've been busy! Want to take a 5-minute break?"
            
            return Suggestion(
                type="take_break",
                message=message,
                action="set_timer",
                priority=2,
                timestamp=datetime.now()
            )
        
        return None
    
    async def _check_morning_briefing(self, context: Context) -> Suggestion | None:
        """Check if morning briefing needed."""
        # Only in early morning
        if context.temporal.time_of_day != TimeOfDay.EARLY_MORNING:
            return None
        
        # Only if there are unread emails or calendar events
        if context.user.emails_unread > 0 or context.user.calendar_next_event:
            message = "Good morning! Want your daily briefing?"
            
            return Suggestion(
                type="morning_briefing",
                message=message,
                action="show_briefing",
                priority=3,
                timestamp=datetime.now()
            )
        
        return None
    
    async def _check_calendar(self, context: Context) -> Suggestion | None:
        """Check for upcoming calendar events."""
        if not context.user.calendar_next_event:
            return None
        
        # TODO: Parse calendar_next_time and check if within 15 minutes
        # For now, just suggest if there's a next event
        
        message = f"Reminder: {context.user.calendar_next_event}"
        
        return Suggestion(
            type="calendar_reminder",
            message=message,
            action=None,
            priority=4,
            timestamp=datetime.now()
        )
    
    async def should_interrupt(self, suggestion: Suggestion) -> bool:
        """
        Determine if a suggestion should interrupt the user.
        
        Args:
            suggestion: The suggestion
            
        Returns:
            bool: Whether to interrupt
        """
        # Only interrupt for high priority
        if suggestion.priority >= 4:
            return True
        
        # Check context
        context = await self.context_engine.get_context()
        
        # Don't interrupt if user is focused
        if context.user.inferred_mood == UserMood.FOCUSED:
            return False
        
        return True
    
    def format_suggestion(self, suggestion: Suggestion) -> str:
        """
        Format suggestion with personality.
        
        Args:
            suggestion: The suggestion
            
        Returns:
            str: Formatted message
        """
        # Add personality to message
        if suggestion.type == "battery_low":
            return f"💡 {suggestion.message}"
        elif suggestion.type == "battery_critical":
            return f"⚠️ {suggestion.message}"
        elif suggestion.type == "take_break":
            return f"😌 {suggestion.message}"
        elif suggestion.type == "morning_briefing":
            return f"☀️ {suggestion.message}"
        elif suggestion.type == "calendar_reminder":
            return f"📅 {suggestion.message}"
        else:
            return suggestion.message


# Singleton instance
_proactive_engine: ProactiveEngine | None = None


def get_proactive_engine() -> ProactiveEngine:
    """Get global proactive engine instance."""
    global _proactive_engine
    if _proactive_engine is None:
        _proactive_engine = ProactiveEngine()
    return _proactive_engine
