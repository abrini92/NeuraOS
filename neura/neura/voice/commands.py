"""
Voice Command Parser - Parses voice input into Flow commands.

Maps natural language voice commands to Flow command syntax.
"""

import logging

from neura.flow.types import FlowCommand

logger = logging.getLogger(__name__)


class VoiceCommandParser:
    """
    Parser for voice commands with NLP support.

    Converts natural language voice input into FlowCommand objects.
    Uses LLM-based NLP for intelligent intent extraction.

    Example:
        >>> parser = VoiceCommandParser()
        >>> cmd = await parser.parse("neura, can you check my emails?")
        >>> print(cmd.name)  # "applescript"
        >>> print(cmd.args)  # ["mail", "list"]
    """
    
    def __init__(self):
        """Initialize parser with NLP support."""
        self.use_nlp = True  # Enable NLP by default

    # Wake words (English + French)
    HOTWORDS = [
        "neura",
        "hey neura",
        "ok neura",
        "hello neura",
        "salut neura",
        "bonjour neura",
        "hé neura",
    ]

    # Intent mapping: keyword → command
    INTENT_MAP = {
        # System commands
        "help": "/help",
        "show help": "/help",
        "status": "/status",
        "show status": "/status",
        "system status": "/status",
        "check status": "/status",
        # Memory commands
        "remember": "/remember",
        "store": "/remember",
        "save": "/remember",
        "recall": "/recall",
        "search": "/recall",
        "find": "/recall",
        # Vault commands
        "unlock vault": "/vault unlock",
        "lock vault": "/vault lock",
        "vault status": "/vault status",
        # Journal commands
        "show journal": "/why",
        "why journal": "/why",
        # AppleScript - Finder commands (English + French)
        "open folder": "/applescript finder open",
        "ouvrir folder": "/applescript finder open",
        "ouvrir le folder": "/applescript finder open",
        "ouvre folder": "/applescript finder open",
        "ouvre le folder": "/applescript finder open",
        "ouvre dossier": "/applescript finder open",
        "ouvrir dossier": "/applescript finder open",
        "list files": "/applescript finder list",
        "liste fichiers": "/applescript finder list",
        "liste les fichiers": "/applescript finder list",
        "montre fichiers": "/applescript finder list",
        "montre les fichiers": "/applescript finder list",
        "list desktop": "/applescript finder list desktop",
        "liste desktop": "/applescript finder list desktop",
        "list downloads": "/applescript finder list downloads",
        "liste téléchargements": "/applescript finder list downloads",
        "disk space": "/applescript finder disk",
        "espace disque": "/applescript finder disk",
        "combien d'espace": "/applescript finder disk",
        "create folder": "/applescript finder create",
        "créer folder": "/applescript finder create",
        "créer dossier": "/applescript finder create",
        "créer un dossier": "/applescript finder create",
        "nouveau dossier": "/applescript finder create",
        "crée dossier": "/applescript finder create",
        "crée un dossier": "/applescript finder create",
        # AppleScript - System commands (English + French)
        "volume": "/applescript system volume",
        "set volume": "/applescript system volume",
        "change volume": "/applescript system volume",
        "mettre volume": "/applescript system volume",
        "changer volume": "/applescript system volume",
        "battery": "/applescript system battery",
        "batterie": "/applescript system battery",
        "battery level": "/applescript system battery",
        "niveau batterie": "/applescript system battery",
        "niveau de batterie": "/applescript system battery",
        "combien de batterie": "/applescript system battery",
        "screenshot": "/applescript system screenshot",
        "take screenshot": "/applescript system screenshot",
        "capture écran": "/applescript system screenshot",
        "prendre capture": "/applescript system screenshot",
        "clipboard": "/applescript system clipboard",
        "get clipboard": "/applescript system clipboard",
        "presse-papier": "/applescript system clipboard",
        # AppleScript - Safari commands (English + French)
        "open url": "/applescript safari open",
        "open website": "/applescript safari open",
        "ouvre site": "/applescript safari open",
        "ouvrir site": "/applescript safari open",
        "ouvre url": "/applescript safari open",
        "search google": "/applescript safari google",
        "cherche google": "/applescript safari google",
        "cherche sur google": "/applescript safari google",
        "recherche google": "/applescript safari google",
        "recherche sur google": "/applescript safari google",
        # AppleScript - Notes commands (English + French)
        "create note": "/applescript notes create",
        "créer note": "/applescript notes create",
        "créer une note": "/applescript notes create",
        "nouvelle note": "/applescript notes create",
        "crée note": "/applescript notes create",
        "list notes": "/applescript notes list",
        "liste notes": "/applescript notes list",
        "liste les notes": "/applescript notes list",
        "montre notes": "/applescript notes list",
        # Navigation (English + French)
        "clear screen": "/clear",
        "clear": "/clear",
        "efface écran": "/clear",
        "exit": "/exit",
        "quit": "/exit",
        "goodbye": "/exit",
        "sortir": "/exit",
        "quitter": "/exit",
        "au revoir": "/exit",
    }

    def __init__(self) -> None:
        """Initialize voice command parser."""
        logger.info("VoiceCommandParser initialized")

    async def parse(self, text: str) -> FlowCommand:
        """
        Parse voice input into FlowCommand.

        Args:
            text: Voice input text

        Returns:
            FlowCommand: Parsed command

        Example:
            >>> parser = VoiceCommandParser()
            >>> cmd = parser.parse("neura, remember project deadline")
            >>> print(cmd.name)  # "remember"
            >>> print(cmd.args)  # ["project deadline"]
        """
        if not text or not text.strip():
            return FlowCommand.parse("")

        text_original = text
        text_lower = text.lower().strip()

        # Remove hotword prefix
        text_lower = self._remove_hotword(text_lower)

        # Remove common filler words
        text_lower = self._remove_fillers(text_lower)

        # Check for direct intent match
        command = self._match_intent(text_lower)
        if command:
            # Extract arguments (everything after the intent)
            args = self._extract_args(text_lower, command)
            return FlowCommand.parse(f"{command} {args}".strip())

        # Check for "ask" intent (questions)
        if self._is_question(text_lower):
            return FlowCommand.parse(f"/ask {text_original}")

        # Default: natural language → /ask
        return FlowCommand.parse(f"/ask {text_original}")

    def _remove_hotword(self, text: str) -> str:
        """Remove hotword from beginning of text."""
        for hotword in self.HOTWORDS:
            if text.startswith(hotword):
                text = text[len(hotword) :].strip()
                # Remove punctuation after hotword
                if text.startswith(","):
                    text = text[1:].strip()
                break
        return text

    def _remove_fillers(self, text: str) -> str:
        """Remove common filler words (English + French)."""
        fillers = [
            # English
            "please",
            "can you",
            "could you",
            "would you",
            "i want to",
            "i'd like to",
            # French
            "s'il te plaît",
            "s'il vous plaît",
            "peux-tu",
            "pouvez-vous",
            "je veux",
            "je voudrais",
            "j'aimerais",
        ]
        for filler in fillers:
            if text.startswith(filler):
                text = text[len(filler) :].strip()
        return text

    def _match_intent(self, text: str) -> str:
        """
        Match text against intent map.

        Returns:
            str: Matched command or None
        """
        for intent, command in self.INTENT_MAP.items():
            if text.startswith(intent):
                return command
        return None

    def _extract_args(self, text: str, command: str) -> str:
        """
        Extract arguments after intent.

        Args:
            text: Input text
            command: Matched command

        Returns:
            str: Arguments string
        """
        # Find the intent that matched
        for intent, cmd in self.INTENT_MAP.items():
            if cmd == command and text.startswith(intent):
                # Return everything after the intent
                args = text[len(intent) :].strip()
                return args
        return ""

    def _is_question(self, text: str) -> bool:
        """Check if text is a question (English + French)."""
        question_words = [
            # English
            "what",
            "who",
            "where",
            "when",
            "why",
            "how",
            "can",
            "could",
            "would",
            "should",
            "is",
            "are",
            "do",
            "does",
            "did",
            # French
            "qu'est-ce",
            "quel",
            "quelle",
            "quels",
            "quelles",
            "qui",
            "où",
            "quand",
            "pourquoi",
            "comment",
            "est-ce",
            "peux-tu",
            "pouvez-vous",
            "c'est quoi",
        ]

        # Check for question mark
        if "?" in text:
            return True

        # Check for question words at start
        first_word = text.split()[0] if text.split() else ""
        return first_word in question_words

    def get_hotwords(self) -> list[str]:
        """Get list of hotwords."""
        return self.HOTWORDS.copy()

    def get_intents(self) -> dict[str, str]:
        """Get intent mapping."""
        return self.INTENT_MAP.copy()
