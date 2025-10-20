"""
Auto-Store - Automatically store important interactions.

Monitors conversations and stores relevant information in memory.
"""

import logging
from datetime import datetime

from neura.core.context import get_context_engine
from neura.core.types import Result

logger = logging.getLogger(__name__)


class AutoStore:
    """
    Automatically store important interactions in memory.
    
    Monitors user interactions and intelligently decides what to store.
    
    Example:
        >>> auto_store = AutoStore()
        >>> await auto_store.process_interaction(
        ...     user="Read my emails",
        ...     assistant="You have 3 emails..."
        ... )
    """
    
    def __init__(self):
        """Initialize auto-store."""
        self.context_engine = get_context_engine()
        self._interaction_count = 0
        logger.info("AutoStore initialized")
    
    async def process_interaction(
        self,
        user_input: str,
        assistant_response: str,
        command_type: str | None = None
    ) -> Result[str]:
        """
        Process an interaction and decide if it should be stored.
        
        Args:
            user_input: What user said/typed
            assistant_response: Neura's response
            command_type: Type of command (ask, remember, etc.)
            
        Returns:
            Result[str]: Memory ID if stored, or skip reason
        """
        self._interaction_count += 1
        
        # Get current context
        context = await self.context_engine.get_context()
        
        # Decide if important enough to store
        should_store = await self._should_store(
            user_input,
            assistant_response,
            command_type,
            context
        )
        
        if not should_store:
            logger.debug(f"Skipping storage for: {user_input[:50]}")
            return Result.success("skipped")
        
        # Build memory content
        memory_content = self._build_memory_content(
            user_input,
            assistant_response,
            command_type,
            context
        )
        
        # Store in memory
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/memory/store",
                    json={"content": memory_content}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memory_id = data.get("id", "unknown")
                    logger.info(f"Auto-stored interaction: {memory_id}")
                    return Result.success(memory_id)
                else:
                    return Result.failure(f"Storage failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Auto-store error: {e}")
            return Result.failure(str(e))
    
    async def _should_store(
        self,
        user_input: str,
        assistant_response: str,
        command_type: str | None,
        context
    ) -> bool:
        """Decide if interaction should be stored."""
        
        # Always store explicit remember commands
        if command_type == "remember":
            return True
        
        # Store questions about personal info
        personal_keywords = [
            "my", "i am", "i'm", "i have", "i like", "i love",
            "my name", "my email", "my phone", "my address"
        ]
        if any(kw in user_input.lower() for kw in personal_keywords):
            return True
        
        # Store important commands (email, calendar, etc.)
        important_commands = ["email", "calendar", "meeting", "event", "deadline"]
        if any(cmd in user_input.lower() for cmd in important_commands):
            return True
        
        # Store if response is long (detailed answer)
        if len(assistant_response) > 200:
            return True
        
        # Store every 5th interaction to maintain conversation history
        if self._interaction_count % 5 == 0:
            return True
        
        # Skip short/trivial interactions
        return False
    
    def _build_memory_content(
        self,
        user_input: str,
        assistant_response: str,
        command_type: str | None,
        context
    ) -> str:
        """Build memory content with context."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_of_day = context.temporal.time_of_day.value
        
        # Format memory entry
        memory = f"""[{timestamp} - {time_of_day}]

User: {user_input}

Neura: {assistant_response}

Context:
- Battery: {context.system.battery_level}%
- Mood: {context.user.inferred_mood.value}
- Day: {context.temporal.day_of_week}
"""
        
        if command_type:
            memory += f"- Command: {command_type}\n"
        
        return memory.strip()


# Singleton
_auto_store: AutoStore | None = None


def get_auto_store() -> AutoStore:
    """Get global auto-store instance."""
    global _auto_store
    if _auto_store is None:
        _auto_store = AutoStore()
    return _auto_store
