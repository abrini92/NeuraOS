"""
Speech-to-Text - Whisper CLI integration with fallback.

Provides STT using OpenAI Whisper CLI if installed.
"""

import logging
import shutil
import subprocess
import time
from pathlib import Path

from neura.core.types import Result
from neura.voice.types import TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperSTT:
    """
    Speech-to-Text using Whisper CLI.

    Uses OpenAI Whisper command-line tool if installed.
    Falls back to placeholder if not available.

    Installation:
        pip install openai-whisper

    Example:
        >>> stt = WhisperSTT()
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
        self.model = model
        self.available = shutil.which("whisper") is not None

        if self.available:
            logger.info(f"WhisperSTT initialized with model={model}")
        else:
            logger.warning("Whisper CLI not installed - STT will use placeholder")

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

        Example:
            >>> stt = WhisperSTT()
            >>> result = await stt.transcribe("recording.wav")
            >>> if result.is_success():
            ...     text = result.data.text
        """
        if not self.available:
            logger.warning("Whisper not available, returning placeholder")
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

            # Build whisper command
            cmd = [
                "whisper",
                str(audio_path),
                "--model",
                self.model,
                "--output_format",
                "txt",
                "--output_dir",
                str(audio_path.parent),
            ]

            if language:
                cmd.extend(["--language", language])

            logger.info(f"Running Whisper: {' '.join(cmd)}")

            # Run whisper (increased timeout for first-time model download)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes for first-time model download
            )

            # Log output for debugging
            if result.stdout:
                logger.debug(f"Whisper stdout: {result.stdout[:200]}")
            if result.stderr:
                logger.debug(f"Whisper stderr: {result.stderr[:200]}")

            if result.returncode != 0:
                error_msg = f"Whisper failed: {result.stderr}"
                logger.error(error_msg)
                return Result.failure(error_msg)

            # Read transcription from output file
            txt_file = audio_path.parent / f"{audio_path.stem}.txt"

            if not txt_file.exists():
                # Try to find any .txt files in the directory
                txt_files = list(audio_path.parent.glob("*.txt"))
                logger.error(f"Output file not found. Expected: {txt_file}")
                logger.error(f"Files in directory: {txt_files}")
                logger.error(f"Whisper stdout: {result.stdout}")
                logger.error(f"Whisper stderr: {result.stderr}")
                return Result.failure(f"Whisper output file not found. Expected: {txt_file.name}")

            with open(txt_file, encoding="utf-8") as f:
                text = f.read().strip()

            duration = time.time() - start_time

            # Clean up output file
            try:
                txt_file.unlink()
            except:
                pass

            logger.info(f"Transcription complete: {len(text)} chars in {duration:.2f}s")

            return Result.success(
                TranscriptionResult(
                    text=text,
                    confidence=None,  # Whisper CLI doesn't provide confidence
                    language=language,
                    duration=duration,
                )
            )

        except subprocess.TimeoutExpired:
            return Result.failure("Whisper transcription timed out")

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
