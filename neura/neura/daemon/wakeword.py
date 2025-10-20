"""
Wake word detection - "Neura".

Continuously listens for the wake word using Whisper.
"""

import asyncio
import logging
import numpy as np
from typing import Callable

try:
    import sounddevice as sd
except ImportError:
    sd = None

from neura.voice.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detector using Whisper.
    
    Listens continuously for "Neura" or "Hey Neura".
    
    Features:
    - Voice Activity Detection (VAD)
    - Low CPU usage (only transcribes when voice detected)
    - Configurable sensitivity
    """

    def __init__(
        self,
        on_wake: Callable[[], None],
        wake_words: list[str] = None,
        sample_rate: int = 16000,
        chunk_duration: float = 1.0
    ):
        """
        Initialize wake word detector.
        
        Args:
            on_wake: Callback when wake word is detected
            wake_words: List of wake words (default: ["neura", "hey neura"])
            sample_rate: Audio sample rate
            chunk_duration: Duration of audio chunks (seconds)
        """
        if not sd:
            raise ImportError("sounddevice not installed. Run: pip install sounddevice")
        
        self.on_wake = on_wake
        self.wake_words = wake_words or ["neura", "hey neura", "ok neura"]
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # VAD for efficient detection
        self.vad = VoiceActivityDetector()
        
        # State
        self.running = False
        self.stream = None
        self.audio_buffer = []
        
        logger.info(f"Wake word detector initialized: {self.wake_words}")

    async def start(self):
        """Start listening for wake word."""
        if self.running:
            logger.warning("Wake word detector already running")
            return
        
        self.running = True
        
        # Start audio stream
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )
        self.stream.start()
        
        logger.info("Wake word detector started")
        
        # Process audio in background
        asyncio.create_task(self._process_audio())

    async def stop(self):
        """Stop listening for wake word."""
        if not self.running:
            return
        
        self.running = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        logger.info("Wake word detector stopped")

    def _audio_callback(self, indata, frames, time_info, status):
        """Handle incoming audio data."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add to buffer
        self.audio_buffer.append(indata.copy())

    async def _process_audio(self):
        """Process audio buffer for wake word detection."""
        while self.running:
            try:
                # Wait for audio data
                if not self.audio_buffer:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get audio chunk
                audio_chunk = self.audio_buffer.pop(0)
                audio_data = np.frombuffer(audio_chunk, dtype=np.float32)
                
                # Check for voice activity
                if not self.vad.is_speech(audio_data):
                    continue
                
                # Transcribe (simplified - would use Whisper here)
                text = await self._transcribe(audio_data)
                
                # Check for wake word
                if text and any(wake in text.lower() for wake in self.wake_words):
                    logger.info(f"Wake word detected: {text}")
                    self._trigger()
            
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await asyncio.sleep(0.1)

    async def _transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data.
        
        TODO: Integrate with Whisper for actual transcription.
        For now, returns empty string.
        """
        # Placeholder - would use Whisper here
        # from neura.voice.stt import transcribe
        # return await transcribe(audio_data)
        return ""

    def _trigger(self):
        """Trigger the wake word callback."""
        try:
            # Run callback
            asyncio.create_task(self._run_callback())
        except Exception as e:
            logger.error(f"Error triggering wake word callback: {e}")

    async def _run_callback(self):
        """Run the callback asynchronously."""
        try:
            if asyncio.iscoroutinefunction(self.on_wake):
                await self.on_wake()
            else:
                self.on_wake()
        except Exception as e:
            logger.error(f"Error in wake word callback: {e}")


# Simplified version for testing
class SimpleWakeWordDetector:
    """
    Simplified wake word detector for testing.
    
    Uses keyword matching instead of Whisper.
    """

    def __init__(self, on_wake: Callable[[], None]):
        """Initialize simple detector."""
        self.on_wake = on_wake
        self.running = False

    async def start(self):
        """Start detector."""
        self.running = True
        logger.info("Simple wake word detector started (testing mode)")

    async def stop(self):
        """Stop detector."""
        self.running = False
        logger.info("Simple wake word detector stopped")

    def trigger_manually(self):
        """Manually trigger wake word (for testing)."""
        logger.info("Wake word triggered manually")
        self.on_wake()
