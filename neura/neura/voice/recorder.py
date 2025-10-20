"""
Audio Recorder - Records audio using sounddevice.

Provides simple audio recording functionality.
"""

import logging
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

from neura.core.types import Result

logger = logging.getLogger(__name__)


class AudioRecorder:
    """
    Audio recorder using sounddevice.

    Records audio from microphone and saves to WAV files.

    Example:
        >>> recorder = AudioRecorder()
        >>> audio = recorder.record(duration=5.0)
        >>> recorder.save_wav(audio, "output.wav")
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        """
        Initialize audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of channels (default: 1 = mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels

        logger.info(f"AudioRecorder initialized: {sample_rate}Hz, {channels} channel(s)")

    def record(self, duration: float) -> Result[np.ndarray]:
        """
        Record audio for specified duration.

        Args:
            duration: Recording duration in seconds

        Returns:
            Result[np.ndarray]: Recorded audio data or error

        Example:
            >>> recorder = AudioRecorder()
            >>> result = recorder.record(5.0)
            >>> if result.is_success():
            ...     audio = result.data
        """
        try:
            logger.info(f"Recording audio for {duration}s...")

            # Record audio
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            )

            # Wait for recording to complete
            sd.wait()

            logger.info(f"Recording complete: {len(audio)} samples")

            return Result.success(audio)

        except Exception as e:
            error_msg = f"Recording failed: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def save_wav(self, audio: np.ndarray, filename: str) -> Result[str]:
        """
        Save audio to WAV file.

        Args:
            audio: Audio data as numpy array
            filename: Output filename

        Returns:
            Result[str]: Filepath or error
        """
        try:
            # Ensure parent directory exists
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Save WAV file
            write(str(filepath), self.sample_rate, audio)

            logger.info(f"Audio saved to {filepath}")

            return Result.success(str(filepath))

        except Exception as e:
            error_msg = f"Failed to save audio: {e}"
            logger.error(error_msg)
            return Result.failure(error_msg)

    def get_default_device_info(self) -> dict:
        """
        Get default input device information.

        Returns:
            dict: Device information
        """
        try:
            device = sd.query_devices(kind="input")
            return {
                "name": device["name"],
                "channels": device["max_input_channels"],
                "sample_rate": device["default_samplerate"],
            }
        except Exception as e:
            logger.error(f"Failed to query device: {e}")
            return {}
