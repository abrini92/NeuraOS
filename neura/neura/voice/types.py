"""
Voice types - Models for voice I/O operations.

Defines Pydantic models for voice operations.
"""

from enum import Enum

from pydantic import BaseModel, Field


class VoiceMode(str, Enum):
    """Voice operation mode."""

    LISTEN = "listen"
    SPEAK = "speak"
    INTERACTIVE = "interactive"


class VoiceConfig(BaseModel):
    """Configuration for Voice module."""

    sample_rate: int = Field(default=16000, description="Audio sample rate (Hz)")
    vad_threshold: float = Field(default=0.01, description="VAD energy threshold")
    hotwords: list[str] = Field(
        default=["neura", "hey neura", "ok neura"], description="Wake words"
    )
    stt_model: str = Field(default="tiny", description="Whisper model size")
    record_duration: float = Field(default=5.0, description="Default recording duration")


class AudioChunk(BaseModel):
    """Audio chunk data."""

    data: bytes = Field(..., description="Raw audio data")
    sample_rate: int = Field(default=16000, description="Sample rate")
    duration: float = Field(..., description="Duration in seconds")
    channels: int = Field(default=1, description="Number of channels")


class TranscriptionResult(BaseModel):
    """Result of speech-to-text operation."""

    text: str = Field(..., description="Transcribed text")
    confidence: float | None = Field(None, description="Confidence score")
    language: str | None = Field(None, description="Detected language")
    duration: float = Field(..., description="Processing duration")


class SynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""

    text: str = Field(..., min_length=1, description="Text to synthesize")
    voice: str | None = Field(None, description="Voice name (optional)")
    rate: int | None = Field(None, description="Speech rate (optional)")


class VoiceStatus(BaseModel):
    """Voice module status."""

    stt_available: bool = Field(..., description="STT engine available")
    tts_available: bool = Field(..., description="TTS engine available")
    stt_engine: str = Field(..., description="STT engine name")
    tts_engine: str = Field(..., description="TTS engine name")
    sample_rate: int = Field(default=16000, description="Current sample rate")
