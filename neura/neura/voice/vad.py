"""
Voice Activity Detection - Simple energy-based VAD.

Detects speech presence in audio using RMS energy threshold.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class SimpleVAD:
    """
    Simple Voice Activity Detection using energy threshold.

    Uses RMS (Root Mean Square) energy to detect speech presence.

    Example:
        >>> vad = SimpleVAD(threshold=0.01)
        >>> audio = np.random.randn(16000) * 0.5
        >>> is_speech = vad.is_speech(audio)
    """

    def __init__(self, threshold: float = 0.01) -> None:
        """
        Initialize VAD.

        Args:
            threshold: Energy threshold for speech detection
        """
        self.threshold = threshold
        logger.info(f"SimpleVAD initialized with threshold={threshold}")

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect if audio chunk contains speech.

        Args:
            audio_chunk: Audio samples as numpy array

        Returns:
            bool: True if speech detected, False otherwise

        Example:
            >>> vad = SimpleVAD()
            >>> loud_audio = np.random.randn(16000) * 0.5
            >>> vad.is_speech(loud_audio)
            True
            >>> quiet_audio = np.random.randn(16000) * 0.001
            >>> vad.is_speech(quiet_audio)
            False
        """
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_chunk**2))

        # Explicit bool cast to avoid np.bool_ type
        is_speech_detected = bool(energy > self.threshold)

        logger.debug(
            f"Audio energy: {energy:.6f}, threshold: {self.threshold}, speech: {is_speech_detected}"
        )

        return is_speech_detected

    def detect_silence(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect if audio chunk is silence.

        Args:
            audio_chunk: Audio samples

        Returns:
            bool: True if silence detected
        """
        return not self.is_speech(audio_chunk)

    def get_energy(self, audio_chunk: np.ndarray) -> float:
        """
        Get RMS energy of audio chunk.

        Args:
            audio_chunk: Audio samples

        Returns:
            float: RMS energy value
        """
        return float(np.sqrt(np.mean(audio_chunk**2)))
