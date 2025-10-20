"""
Context Engine - Understand current user context.

Provides situational awareness for proactive assistance.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TimeOfDay(Enum):
    """Time of day categories."""
    EARLY_MORNING = "early_morning"  # 5-8am
    MORNING = "morning"              # 8-12pm
    AFTERNOON = "afternoon"          # 12-5pm
    EVENING = "evening"              # 5-9pm
    NIGHT = "night"                  # 9pm-5am


class UserMood(Enum):
    """Inferred user mood/state."""
    FOCUSED = "focused"      # Working, concentrated
    RELAXED = "relaxed"      # Casual browsing
    BUSY = "busy"            # Many tasks
    TIRED = "tired"          # Low activity
    UNKNOWN = "unknown"


@dataclass
class SystemContext:
    """Current system state."""
    battery_level: int
    battery_charging: bool
    wifi_connected: bool
    active_app: str | None
    screen_locked: bool


@dataclass
class TemporalContext:
    """Time-based context."""
    time_of_day: TimeOfDay
    day_of_week: str
    is_weekend: bool
    is_work_hours: bool


@dataclass
class UserContext:
    """User activity context."""
    emails_unread: int
    calendar_next_event: str | None
    calendar_next_time: str | None
    recent_commands: list[str]
    inferred_mood: UserMood


@dataclass
class Context:
    """Complete context snapshot."""
    timestamp: datetime
    system: SystemContext
    temporal: TemporalContext
    user: UserContext
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "system": {
                "battery_level": self.system.battery_level,
                "battery_charging": self.system.battery_charging,
                "wifi_connected": self.system.wifi_connected,
                "active_app": self.system.active_app,
                "screen_locked": self.system.screen_locked,
            },
            "temporal": {
                "time_of_day": self.temporal.time_of_day.value,
                "day_of_week": self.temporal.day_of_week,
                "is_weekend": self.temporal.is_weekend,
                "is_work_hours": self.temporal.is_work_hours,
            },
            "user": {
                "emails_unread": self.user.emails_unread,
                "calendar_next_event": self.user.calendar_next_event,
                "calendar_next_time": self.user.calendar_next_time,
                "recent_commands": self.user.recent_commands,
                "inferred_mood": self.user.inferred_mood.value,
            }
        }


class ContextEngine:
    """
    Engine for understanding current context.
    
    Provides situational awareness by combining:
    - System state (battery, network, etc.)
    - Temporal context (time, day, etc.)
    - User activity (emails, calendar, etc.)
    
    Example:
        >>> engine = ContextEngine()
        >>> context = await engine.get_context()
        >>> if context.system.battery_level < 20:
        ...     suggest_power_saving()
    """
    
    def __init__(self):
        """Initialize context engine."""
        self._recent_commands: list[str] = []
        logger.info("ContextEngine initialized")
    
    async def get_context(self) -> Context:
        """
        Get current context snapshot.
        
        Returns:
            Context: Complete context information
        """
        now = datetime.now()
        
        # Gather all context components
        system_ctx = await self._get_system_context()
        temporal_ctx = self._get_temporal_context(now)
        user_ctx = await self._get_user_context()
        
        context = Context(
            timestamp=now,
            system=system_ctx,
            temporal=temporal_ctx,
            user=user_ctx
        )
        
        logger.debug(f"Context: {temporal_ctx.time_of_day.value}, "
                    f"battery={system_ctx.battery_level}%, "
                    f"mood={user_ctx.inferred_mood.value}")
        
        return context
    
    async def _get_system_context(self) -> SystemContext:
        """Get system state context."""
        try:
            from neura.motor.applescript.system import SystemScripts
            from neura.motor.applescript.executor import AppleScriptExecutor
            
            executor = AppleScriptExecutor()
            
            # Get battery level
            battery_result = await executor.execute(SystemScripts.get_battery())
            battery_level = 100  # Default
            battery_charging = False
            
            if battery_result.is_success():
                # Parse battery info
                battery_info = battery_result.data
                if "%" in battery_info:
                    try:
                        battery_level = int(battery_info.split("%")[0].split()[-1])
                    except:
                        pass
                battery_charging = "charging" in battery_info.lower()
            
            return SystemContext(
                battery_level=battery_level,
                battery_charging=battery_charging,
                wifi_connected=True,  # TODO: Detect WiFi
                active_app=None,      # TODO: Get active app
                screen_locked=False   # TODO: Detect lock
            )
        
        except Exception as e:
            logger.error(f"Error getting system context: {e}")
            return SystemContext(
                battery_level=100,
                battery_charging=False,
                wifi_connected=True,
                active_app=None,
                screen_locked=False
            )
    
    def _get_temporal_context(self, now: datetime) -> TemporalContext:
        """Get time-based context."""
        hour = now.hour
        
        # Determine time of day
        if 5 <= hour < 8:
            time_of_day = TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            time_of_day = TimeOfDay.MORNING
        elif 12 <= hour < 17:
            time_of_day = TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            time_of_day = TimeOfDay.EVENING
        else:
            time_of_day = TimeOfDay.NIGHT
        
        # Day info
        day_of_week = now.strftime("%A")
        is_weekend = now.weekday() >= 5
        is_work_hours = 9 <= hour < 18 and not is_weekend
        
        return TemporalContext(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            is_work_hours=is_work_hours
        )
    
    async def _get_user_context(self) -> UserContext:
        """Get user activity context."""
        # TODO: Get actual email count
        emails_unread = 0
        
        # TODO: Get calendar info
        calendar_next_event = None
        calendar_next_time = None
        
        # Infer mood from recent activity
        mood = self._infer_mood()
        
        return UserContext(
            emails_unread=emails_unread,
            calendar_next_event=calendar_next_event,
            calendar_next_time=calendar_next_time,
            recent_commands=self._recent_commands[-10:],
            inferred_mood=mood
        )
    
    def _infer_mood(self) -> UserMood:
        """Infer user mood from activity."""
        # Simple heuristic based on command frequency
        if len(self._recent_commands) > 5:
            return UserMood.BUSY
        elif len(self._recent_commands) > 2:
            return UserMood.FOCUSED
        elif len(self._recent_commands) > 0:
            return UserMood.RELAXED
        else:
            return UserMood.UNKNOWN
    
    def add_command(self, command: str) -> None:
        """Track user command for mood inference."""
        self._recent_commands.append(command)
        if len(self._recent_commands) > 50:
            self._recent_commands = self._recent_commands[-50:]
    
    async def should_suggest(self, suggestion_type: str) -> bool:
        """
        Determine if a suggestion should be made based on context.
        
        Args:
            suggestion_type: Type of suggestion (battery, break, etc.)
            
        Returns:
            bool: Whether to make the suggestion
        """
        context = await self.get_context()
        
        if suggestion_type == "battery_low":
            return (context.system.battery_level < 20 and 
                   not context.system.battery_charging)
        
        elif suggestion_type == "take_break":
            return (context.user.inferred_mood == UserMood.BUSY and
                   context.temporal.is_work_hours)
        
        elif suggestion_type == "check_calendar":
            return (context.temporal.time_of_day == TimeOfDay.MORNING and
                   context.user.calendar_next_event is not None)
        
        return False


# Singleton instance
_context_engine: ContextEngine | None = None


def get_context_engine() -> ContextEngine:
    """Get global context engine instance."""
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextEngine()
    return _context_engine
