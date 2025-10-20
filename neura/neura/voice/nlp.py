"""
Natural Language Parsing - Understand intent from natural language.

Uses Cortex to extract intent from free-form text.
"""

import json
import logging
from dataclasses import dataclass

from neura.core.types import Result

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Parsed intent from natural language."""
    action: str
    category: str
    parameters: dict
    confidence: float


class NaturalLanguageParser:
    """
    Parse natural language to extract intent.
    
    Uses LLM to understand what user wants, not just keyword matching.
    
    Example:
        >>> parser = NaturalLanguageParser()
        >>> intent = await parser.parse("Can you please read my emails?")
        >>> print(intent.action)  # "list_emails"
    """
    
    INTENT_PROMPT = """Extract the user's intent from their natural language request.

Available intents:
- list_emails: Check inbox
- read_email: Read specific email
- send_email: Compose and send email
- list_calendar: Show calendar events
- create_event: Add calendar event
- open_url: Open website
- search_google: Search on Google
- get_battery: Check battery level
- list_files: List files in folder
- open_folder: Open Finder folder
- get_volume: Check system volume
- set_volume: Change volume
- take_screenshot: Capture screen
- create_note: Make a note
- list_notes: Show notes

User request: "{text}"

Respond with ONLY valid JSON in this exact format:
{{
  "action": "intent_name",
  "category": "mail|calendar|finder|system|safari|notes",
  "parameters": {{}},
  "confidence": 0.95
}}

Examples:
"Can you check my emails?" → {{"action": "list_emails", "category": "mail", "parameters": {{}}, "confidence": 0.95}}
"What's my battery at?" → {{"action": "get_battery", "category": "system", "parameters": {{}}, "confidence": 0.98}}
"Open my documents folder" → {{"action": "open_folder", "category": "finder", "parameters": {{"folder": "Documents"}}, "confidence": 0.92}}
"""
    
    def __init__(self):
        """Initialize NLP parser."""
        logger.info("NaturalLanguageParser initialized")
    
    async def parse(self, text: str) -> Result[Intent]:
        """
        Parse natural language to extract intent.
        
        Args:
            text: Natural language input
            
        Returns:
            Result[Intent]: Parsed intent or error
        """
        if not text or not text.strip():
            return Result.failure("Empty input")
        
        try:
            # Use Cortex to parse
            import httpx
            
            prompt = self.INTENT_PROMPT.format(text=text)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/cortex/generate",
                    json={
                        "prompt": prompt,
                        "temperature": 0.1,  # Low temp for consistent parsing
                        "max_tokens": 200,
                        "stream": False
                    }
                )
                
                if response.status_code != 200:
                    return Result.failure(f"Cortex error: {response.status_code}")
                
                data = response.json()
                llm_response = data.get("text", "").strip()
                
                # Parse JSON response
                try:
                    # Extract JSON from response (might have extra text)
                    json_start = llm_response.find("{")
                    json_end = llm_response.rfind("}") + 1
                    
                    if json_start == -1 or json_end == 0:
                        return Result.failure("No JSON in response")
                    
                    json_str = llm_response[json_start:json_end]
                    intent_data = json.loads(json_str)
                    
                    intent = Intent(
                        action=intent_data.get("action", "unknown"),
                        category=intent_data.get("category", "unknown"),
                        parameters=intent_data.get("parameters", {}),
                        confidence=intent_data.get("confidence", 0.5)
                    )
                    
                    logger.info(f"Parsed intent: {intent.action} (confidence: {intent.confidence})")
                    return Result.success(intent)
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    logger.debug(f"Response was: {llm_response}")
                    return Result.failure(f"Failed to parse intent: {e}")
        
        except Exception as e:
            logger.error(f"NLP parse error: {e}")
            return Result.failure(f"Parse error: {e}")
    
    async def parse_with_fallback(self, text: str) -> Result[Intent]:
        """
        Parse with fallback to keyword matching.
        
        Args:
            text: Natural language input
            
        Returns:
            Result[Intent]: Parsed intent or error
        """
        # Try NLP first
        result = await self.parse(text)
        
        if result.is_success() and result.data.confidence > 0.7:
            return result
        
        # Fallback to keyword matching
        logger.info("NLP confidence low, using keyword fallback")
        return self._keyword_fallback(text)
    
    def _keyword_fallback(self, text: str) -> Result[Intent]:
        """Fallback to simple keyword matching."""
        text_lower = text.lower()
        
        # Email keywords
        if any(word in text_lower for word in ["email", "inbox", "mail"]):
            if any(word in text_lower for word in ["read", "check", "show"]):
                return Result.success(Intent(
                    action="list_emails",
                    category="mail",
                    parameters={},
                    confidence=0.8
                ))
        
        # Battery keywords
        if any(word in text_lower for word in ["battery", "power", "charge"]):
            return Result.success(Intent(
                action="get_battery",
                category="system",
                parameters={},
                confidence=0.85
            ))
        
        # Files keywords
        if any(word in text_lower for word in ["files", "folder", "finder"]):
            if "open" in text_lower:
                return Result.success(Intent(
                    action="open_folder",
                    category="finder",
                    parameters={"folder": "Desktop"},
                    confidence=0.75
                ))
            else:
                return Result.success(Intent(
                    action="list_files",
                    category="finder",
                    parameters={"folder": "Desktop"},
                    confidence=0.75
                ))
        
        # Calendar keywords
        if any(word in text_lower for word in ["calendar", "meeting", "event"]):
            return Result.success(Intent(
                action="list_calendar",
                category="calendar",
                parameters={},
                confidence=0.8
            ))
        
        # Default: unknown
        return Result.failure("Could not understand intent")


# Singleton
_nlp_parser: NaturalLanguageParser | None = None


def get_nlp_parser() -> NaturalLanguageParser:
    """Get global NLP parser instance."""
    global _nlp_parser
    if _nlp_parser is None:
        _nlp_parser = NaturalLanguageParser()
    return _nlp_parser
