"""
Text-to-Speech - System TTS using say (macOS) or espeak (Linux).

Provides simple TTS using built-in system commands.
"""

import logging
import platform
import shutil
import subprocess

from neura.core.types import Result

logger = logging.getLogger(__name__)


class SystemTTS:
    """
    System Text-to-Speech using native commands.

    Uses:
    - macOS: `say` command (built-in)
    - Linux: `espeak` command (if installed)
    - Windows: Not supported in MVP

    Example:
        >>> tts = SystemTTS()
        >>> await tts.synthesize("Hello, world!")
    """

    def __init__(self) -> None:
        """Initialize system TTS."""
        self.system = platform.system()
        self.available = self._check_availability()

        if self.available:
            logger.info(f"SystemTTS initialized on {self.system}")
        else:
            logger.warning(f"TTS not available on {self.system}")

    def _check_availability(self) -> bool:
        """
        Check if TTS is available on current system.

        Returns:
            bool: True if TTS available
        """
        if self.system == "Darwin":  # macOS
            # say is built-in on macOS
            return True
        elif self.system == "Linux":
            # Check if espeak is installed
            return shutil.which("espeak") is not None
        else:
            return False

    async def synthesize(self, text: str, voice: str | None = None, rate: int | None = None) -> Result[bool]:
        """
        Synthesize text to speech.

        Args:
            text: Text to speak
            voice: Voice name (optional, system-dependent)
            rate: Speech rate (optional, words per minute)

        Returns:
            Result[bool]: Success or error

        Example:
            >>> tts = SystemTTS()
            >>> result = await tts.synthesize("Hello, Neura!")
            >>> if result.is_success():
            ...     print("Speech completed")
        """
        if not self.available:
            return Result.failure("TTS not available on this system")

        if not text or not text.strip():
            return Result.failure("Text cannot be empty")

        try:
            if self.system == "Darwin":  # macOS
                return await self._synthesize_macos(text, voice, rate)
            elif self.system == "Linux":
                return await self._synthesize_linux(text)
            else:
                return Result.failure(f"TTS not supported on {self.system}")

        except Exception as e:
            error_msg = f"TTS error: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def _synthesize_macos(
        self, text: str, voice: str | None = None, rate: int | None = None
    ) -> Result[bool]:
        """Synthesize using macOS `say` command."""
        try:
            cmd = ["say"]

            if voice:
                cmd.extend(["-v", voice])

            if rate:
                cmd.extend(["-r", str(rate)])

            cmd.append(text)

            logger.debug(f"Running: {' '.join(cmd)}")

            subprocess.run(cmd, check=True, capture_output=True, text=True)

            logger.info(f"TTS completed: {len(text)} chars")
            return Result.success(True)

        except subprocess.CalledProcessError as e:
            error_msg = f"say command failed: {e.stderr}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    async def _synthesize_linux(self, text: str) -> Result[bool]:
        """Synthesize using Linux `espeak` command."""
        try:
            subprocess.run(["espeak", text], check=True, capture_output=True, text=True)

            logger.info(f"TTS completed: {len(text)} chars")
            return Result.success(True)

        except subprocess.CalledProcessError as e:
            error_msg = f"espeak command failed: {e.stderr}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def get_available_voices(self) -> list[str]:
        """
        Get list of available voices.

        Returns:
            list: Voice names (macOS only)
        """
        if self.system != "Darwin":
            return []

        try:
            result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)

            voices = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    # Extract voice name (first word)
                    voice_name = line.split()[0]
                    voices.append(voice_name)

            return voices

        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.available
