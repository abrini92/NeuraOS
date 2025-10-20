"""
Personality Engine - Consistent Neura personality.

Provides natural, empathetic responses with consistent character.
"""

import logging
import random
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseCategory(Enum):
    """Response categories."""
    SUCCESS = "success"
    THINKING = "thinking"
    ERROR = "error"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    CONFIRMATION = "confirmation"
    CLARIFICATION = "clarification"
    EMPATHY = "empathy"


class NeuraPersonality:
    """
    Neura's personality engine.
    
    Traits:
    - Helpful (0.9) - Always tries to assist
    - Concise (0.8) - Brief, not verbose
    - Friendly (0.9) - Warm and approachable
    - Professional (0.7) - Competent but not stiff
    - Humorous (0.4) - Occasional light humor
    
    Example:
        >>> personality = NeuraPersonality()
        >>> response = personality.get_response("success")
        >>> print(response)  # "Done" or "Got it" or "Perfect"
    """
    
    # Response templates by category
    RESPONSES = {
        ResponseCategory.SUCCESS: [
            "Done",
            "Got it",
            "All set",
            "Perfect",
            "Complete",
            "Ready",
        ],
        
        ResponseCategory.THINKING: [
            "Let me check...",
            "One moment...",
            "Hmm, let me see...",
            "Checking...",
            "Looking into it...",
        ],
        
        ResponseCategory.ERROR: [
            "Hmm, something's off",
            "That didn't work",
            "Let me try again",
            "I couldn't do that",
            "Something went wrong",
        ],
        
        ResponseCategory.GREETING: [
            "Hello",
            "Hey there",
            "Hi",
            "Good to see you",
            "I'm listening",
        ],
        
        ResponseCategory.GOODBYE: [
            "Goodbye",
            "See you",
            "Anytime",
            "Take care",
            "Until next time",
        ],
        
        ResponseCategory.CONFIRMATION: [
            "Should I proceed?",
            "Want me to continue?",
            "Is that right?",
            "Confirm?",
            "Ready to go?",
        ],
        
        ResponseCategory.CLARIFICATION: [
            "I didn't quite catch that",
            "Could you rephrase?",
            "What did you mean?",
            "Can you clarify?",
            "I'm not sure I understand",
        ],
        
        ResponseCategory.EMPATHY: [
            "I understand",
            "I hear you",
            "That makes sense",
            "I get it",
            "Understood",
        ],
    }
    
    def __init__(self):
        """Initialize personality engine."""
        self.traits = {
            "helpful": 0.9,
            "concise": 0.8,
            "friendly": 0.9,
            "professional": 0.7,
            "humorous": 0.4,
        }
        logger.info("NeuraPersonality initialized")
    
    def get_response(self, category: str | ResponseCategory) -> str:
        """
        Get a response from a category.
        
        Args:
            category: Response category
            
        Returns:
            str: Random response from category
        """
        if isinstance(category, str):
            try:
                category = ResponseCategory(category)
            except ValueError:
                logger.warning(f"Unknown category: {category}")
                return "Okay"
        
        responses = self.RESPONSES.get(category, ["Okay"])
        return random.choice(responses)
    
    def format_success(self, action: str, details: str | None = None) -> str:
        """
        Format a success message.
        
        Args:
            action: Action completed
            details: Optional details
            
        Returns:
            str: Formatted success message
        """
        base = self.get_response(ResponseCategory.SUCCESS)
        
        if details:
            return f"{base}. {details}"
        else:
            return f"{base}"
    
    def format_error(self, error: str, suggestion: str | None = None) -> str:
        """
        Format an error message empathetically.
        
        Args:
            error: Error description
            suggestion: Optional suggestion
            
        Returns:
            str: Formatted error message
        """
        base = self.get_response(ResponseCategory.ERROR)
        
        # Make error user-friendly
        friendly_error = self._make_friendly(error)
        
        if suggestion:
            return f"{base}. {friendly_error}. {suggestion}"
        else:
            return f"{base}. {friendly_error}"
    
    def _make_friendly(self, technical_error: str) -> str:
        """Convert technical error to friendly message."""
        error_lower = technical_error.lower()
        
        # Common error patterns
        if "timeout" in error_lower:
            return "That's taking longer than expected"
        elif "connection" in error_lower or "connect" in error_lower:
            return "I couldn't connect"
        elif "not found" in error_lower:
            return "I couldn't find that"
        elif "permission" in error_lower or "denied" in error_lower:
            return "I don't have access to that"
        elif "invalid" in error_lower:
            return "That doesn't seem right"
        else:
            return "Something unexpected happened"
    
    def format_thinking(self, task: str | None = None) -> str:
        """
        Format a thinking/processing message.
        
        Args:
            task: Optional task description
            
        Returns:
            str: Formatted thinking message
        """
        base = self.get_response(ResponseCategory.THINKING)
        
        if task:
            return f"{base} {task}"
        else:
            return base
    
    def format_confirmation(self, action: str, details: str | None = None) -> str:
        """
        Format a confirmation request.
        
        Args:
            action: Action to confirm
            details: Optional details
            
        Returns:
            str: Formatted confirmation message
        """
        if details:
            return f"{action}: {details}. {self.get_response(ResponseCategory.CONFIRMATION)}"
        else:
            return f"{action}. {self.get_response(ResponseCategory.CONFIRMATION)}"
    
    def contextualize_response(self, base_response: str, context: dict) -> str:
        """
        Add context to a response.
        
        Args:
            base_response: Base response
            context: Context information
            
        Returns:
            str: Contextualized response
        """
        # Add battery warning if low
        if context.get("battery_level", 100) < 20:
            base_response += " (Battery low at {}%)".format(context["battery_level"])
        
        # Add time-aware greeting
        time_of_day = context.get("time_of_day")
        if time_of_day == "morning":
            base_response = f"Good morning! {base_response}"
        elif time_of_day == "evening":
            base_response = f"Good evening! {base_response}"
        
        return base_response


# Singleton instance
_personality: NeuraPersonality | None = None


def get_personality() -> NeuraPersonality:
    """Get global personality instance."""
    global _personality
    if _personality is None:
        _personality = NeuraPersonality()
    return _personality
