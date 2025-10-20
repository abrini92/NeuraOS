"""
Speech-to-Text - Whisper Python API (more reliable than CLI).

Uses OpenAI Whisper Python API directly.
"""

import logging
import time
from pathlib import Path

from neura.core.types import Result
from neura.voice.types import TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperSTTPython:
    """
    Speech-to-Text using Whisper Python API.

    More reliable than CLI version.

    Example:
        >>> stt = WhisperSTTPython()
        >>> result = await stt.transcribe("audio.wav")
        >>> if result.is_success():
        ...     print(result.data.text)
    """

    def __init__(self, model: str = "tiny") -> None:
        """
        Initialize Whisper STT.

        Args:
            model: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model
        self.model = None
        self.available = False

        try:
            import whisper

            self.model = whisper.load_model(model)
            self.available = True
            logger.info(f"WhisperSTTPython initialized with model={model}")
        except ImportError:
            logger.warning("Whisper package not installed - STT not available")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    async def transcribe(
        self, audio_file: str, language: str | None = None
    ) -> Result[TranscriptionResult]:
        """
        Transcribe audio file to text.

        Args:
            audio_file: Path to audio file (WAV format recommended)
            language: Language code (optional, e.g., 'en', 'fr')

        Returns:
            Result[TranscriptionResult]: Transcription or error
        """
        if not self.available or self.model is None:
            logger.warning("Whisper not available")
            return Result.success(
                TranscriptionResult(
                    text="[STT not available - install Whisper: pip install openai-whisper]",
                    confidence=0.0,
                    language=None,
                    duration=0.0,
                )
            )

        audio_path = Path(audio_file)
        if not audio_path.exists():
            return Result.failure(f"Audio file not found: {audio_file}")

        try:
            start_time = time.time()

            logger.info(f"Transcribing with Whisper model={self.model_name}")

            # Transcribe using Whisper Python API
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                fp16=False,  # Disable FP16 for CPU compatibility
            )

            text = result["text"].strip()
            detected_lang = result.get("language")

            duration = time.time() - start_time

            logger.info(f"Transcription complete: '{text}' ({len(text)} chars in {duration:.2f}s)")

            return Result.success(
                TranscriptionResult(
                    text=text, confidence=None, language=detected_lang, duration=duration
                )
            )

        except Exception as e:
            error_msg = f"STT error: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def is_available(self) -> bool:
        """Check if Whisper is available."""
        return self.available

    def get_supported_models(self) -> list[str]:
        """Get list of supported Whisper models."""
        return ["tiny", "base", "small", "medium", "large"]
