"""
Voice API Router - REST endpoints for voice operations.

Provides API for TTS, STT, and voice status.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from neura.voice.stt import WhisperSTT
from neura.voice.tts import SystemTTS
from neura.voice.types import SynthesisRequest, VoiceStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
_stt = None
_tts = None


def get_stt() -> WhisperSTT:
    """Get global STT instance."""
    global _stt
    if _stt is None:
        _stt = WhisperSTT()
    return _stt


def get_tts() -> SystemTTS:
    """Get global TTS instance."""
    global _tts
    if _tts is None:
        _tts = SystemTTS()
    return _tts


@router.get("/status", response_model=VoiceStatus)
async def get_status() -> dict:
    """
    Get voice module status.

    Returns STT and TTS availability.
    """
    stt = get_stt()
    tts = get_tts()

    return VoiceStatus(
        stt_available=stt.is_available(),
        tts_available=tts.is_available(),
        stt_engine="Whisper CLI" if stt.is_available() else "None",
        tts_engine="say (macOS)" if tts.is_available() else "None",
        sample_rate=16000,
    )


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text.

    Upload an audio file and get text transcription.

    Args:
        file: Audio file (WAV format recommended)

    Returns:
        JSON with transcription result
    """
    stt = get_stt()

    if not stt.is_available():
        return JSONResponse(
            status_code=503,
            content={
                "error": "STT not available",
                "message": "Install Whisper: pip install openai-whisper",
            },
        )

    try:
        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe
        result = await stt.transcribe(tmp_path)

        # Clean up
        Path(tmp_path).unlink(missing_ok=True)

        if result.is_failure():
            raise HTTPException(status_code=500, detail=result.error)

        transcription = result.data

        return {
            "text": transcription.text,
            "confidence": transcription.confidence,
            "language": transcription.language,
            "duration": transcription.duration,
        }

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(request: SynthesisRequest) -> dict:
    """
    Synthesize text to speech.

    Converts text to spoken audio using system TTS.

    Args:
        request: SynthesisRequest with text and options

    Returns:
        JSON with success status
    """
    tts = get_tts()

    if not tts.is_available():
        return JSONResponse(
            status_code=503,
            content={"error": "TTS not available", "message": "TTS not supported on this system"},
        )

    try:
        result = await tts.synthesize(text=request.text, voice=request.voice, rate=request.rate)

        if result.is_failure():
            raise HTTPException(status_code=500, detail=result.error)

        return {"success": True, "text": request.text, "length": len(request.text)}

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices() -> dict:
    """
    List available TTS voices.

    Returns list of available voices (macOS only).
    """
    tts = get_tts()

    if not tts.is_available():
        return JSONResponse(status_code=503, content={"error": "TTS not available"})

    voices = tts.get_available_voices()

    return {"voices": voices, "count": len(voices)}
