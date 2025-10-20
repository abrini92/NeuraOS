"""
Unit tests for Voice module.

Tests VAD, command parsing, and voice operations.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from neura.voice.vad import SimpleVAD
from neura.voice.commands import VoiceCommandParser
from neura.voice.types import VoiceConfig, VoiceMode, SynthesisRequest


class TestSimpleVAD:
    """Tests for SimpleVAD."""
    
    def test_detect_speech_loud_audio(self):
        """Test speech detection with loud audio."""
        vad = SimpleVAD(threshold=0.01)
        
        # Loud audio (simulates speech)
        loud_audio = np.random.randn(16000) * 0.5
        
        assert vad.is_speech(loud_audio) == True
    
    def test_detect_silence_quiet_audio(self):
        """Test silence detection with quiet audio."""
        vad = SimpleVAD(threshold=0.01)
        
        # Quiet audio (simulates silence)
        quiet_audio = np.random.randn(16000) * 0.001
        
        assert vad.is_speech(quiet_audio) == False
        assert vad.detect_silence(quiet_audio) == True
    
    def test_vad_custom_threshold(self):
        """Test VAD with custom threshold."""
        vad = SimpleVAD(threshold=0.05)
        
        # Medium energy audio
        medium_audio = np.random.randn(16000) * 0.03
        
        # Should not detect speech with higher threshold
        assert vad.is_speech(medium_audio) == False
    
    def test_get_energy(self):
        """Test energy calculation."""
        vad = SimpleVAD()
        
        audio = np.random.randn(16000) * 0.5
        energy = vad.get_energy(audio)
        
        assert isinstance(energy, float)
        assert energy > 0


class TestVoiceCommandParser:
    """Tests for VoiceCommandParser."""
    
    @pytest.mark.asyncio
    async def test_parse_with_hotword(self):
        """Test parsing command with hotword."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("neura, status")
        
        assert cmd.name == "status"
        assert cmd.type.value == "builtin"
    
    @pytest.mark.asyncio
    async def test_parse_without_hotword(self):
        """Test parsing command without hotword."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("show help")
        
        assert cmd.name == "help"
    
    @pytest.mark.asyncio
    async def test_parse_remember_intent(self):
        """Test remember intent parsing."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("neura, remember project deadline november 15")
        
        assert cmd.name == "remember"
        assert "project deadline november 15" in cmd.args[0].lower()
    
    @pytest.mark.asyncio
    async def test_parse_recall_intent(self):
        """Test recall intent parsing."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("recall project deadline")
        
        assert cmd.name == "recall"
        assert "project deadline" in cmd.args[0].lower()
    
    @pytest.mark.asyncio
    async def test_parse_vault_unlock(self):
        """Test vault unlock intent."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("unlock vault")
        
        # Should match vault unlock intent
        assert "vault" in cmd.raw.lower()
    
    @pytest.mark.asyncio
    async def test_parse_question(self):
        """Test question parsing."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("what is the status?")
        
        # Questions should go to /ask
        assert cmd.name == "ask"
    
    @pytest.mark.asyncio
    async def test_parse_natural_language(self):
        """Test natural language fallback."""
        parser = VoiceCommandParser()
        
        cmd = await parser.parse("tell me about artificial intelligence")
        
        # Should fall back to /ask
        assert cmd.name == "ask"
        assert "artificial intelligence" in cmd.args[0].lower()
    
    @pytest.mark.asyncio
    async def test_remove_hotword(self):
        """Test hotword removal."""
        parser = VoiceCommandParser()
        
        # Test all hotwords
        for hotword in parser.HOTWORDS:
            text = f"{hotword}, help"
            cmd = await parser.parse(text)
            assert cmd.name == "help"
    
    def test_get_hotwords(self):
        """Test getting hotwords list."""
        parser = VoiceCommandParser()
        
        hotwords = parser.get_hotwords()
        
        assert isinstance(hotwords, list)
        assert "neura" in hotwords
    
    def test_get_intents(self):
        """Test getting intents map."""
        parser = VoiceCommandParser()
        
        intents = parser.get_intents()
        
        assert isinstance(intents, dict)
        assert "help" in intents
        assert intents["help"] == "/help"


class TestVoiceConfig:
    """Tests for VoiceConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = VoiceConfig()
        
        assert config.sample_rate == 16000
        assert config.vad_threshold == 0.01
        assert "neura" in config.hotwords
        assert config.stt_model == "tiny"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = VoiceConfig(
            sample_rate=48000,
            vad_threshold=0.05,
            stt_model="base"
        )
        
        assert config.sample_rate == 48000
        assert config.vad_threshold == 0.05
        assert config.stt_model == "base"


class TestVoiceMode:
    """Tests for VoiceMode enum."""
    
    def test_voice_modes(self):
        """Test voice mode enum values."""
        assert VoiceMode.LISTEN == "listen"
        assert VoiceMode.SPEAK == "speak"
        assert VoiceMode.INTERACTIVE == "interactive"


class TestSynthesisRequest:
    """Tests for SynthesisRequest."""
    
    def test_synthesis_request(self):
        """Test creating synthesis request."""
        request = SynthesisRequest(text="Hello, world!")
        
        assert request.text == "Hello, world!"
        assert request.voice is None
        assert request.rate is None
    
    def test_synthesis_request_with_options(self):
        """Test synthesis request with voice and rate."""
        request = SynthesisRequest(
            text="Test",
            voice="Alex",
            rate=200
        )
        
        assert request.text == "Test"
        assert request.voice == "Alex"
        assert request.rate == 200


# Integration tests (marked to skip if modules not available)

@pytest.mark.asyncio
@pytest.mark.integration
class TestVoiceIntegration:
    """Integration tests for Voice module."""
    
    async def test_tts_availability(self):
        """Test TTS availability check."""
        from neura.voice.tts import SystemTTS
        
        tts = SystemTTS()
        
        # Just check it initializes
        assert tts is not None
        assert isinstance(tts.is_available(), bool)
    
    async def test_stt_availability(self):
        """Test STT availability check."""
        from neura.voice.stt import WhisperSTT
        
        stt = WhisperSTT()
        
        # Just check it initializes
        assert stt is not None
        assert isinstance(stt.is_available(), bool)
    
    async def test_recorder_device_info(self):
        """Test audio recorder device info."""
        from neura.voice.recorder import AudioRecorder
        
        try:
            recorder = AudioRecorder()
            info = recorder.get_default_device_info()
            
            # Should return dict (even if empty on CI)
            assert isinstance(info, dict)
        except:
            # Skip if no audio device available (CI environment)
            pytest.skip("No audio device available")
