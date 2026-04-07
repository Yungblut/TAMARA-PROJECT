"""
TAMARA TTS Engine Module
Text-to-speech engine using Kokoro + Misaki.
"""

import base64
import io
import os

import soundfile as sf
import structlog

from .config import get_settings

log = structlog.get_logger("tamara.tts")


class TTSEngine:
    """
    Text-to-Speech engine using Kokoro ONNX and Misaki G2P.

    Converts text to audio using phonemization for better pronunciation.
    """

    def __init__(self):
        self._kokoro = None
        self._g2p = None
        self._voice_style = None
        self._ready = False
        self._config = get_settings().tts

    @property
    def is_ready(self) -> bool:
        """Indicates if the engine is ready to generate audio."""
        return self._ready

    def initialize(self) -> bool:
        """
        Initialize the TTS engine.

        Returns:
            True if initialization was successful, False otherwise.
        """
        if self._ready:
            return True

        config = self._config

        # Verify model files exist
        if not os.path.exists(config.model_path):
            log.error("Model not found", path=config.model_path)
            return False

        if not os.path.exists(config.voices_path):
            log.error("Voices not found", path=config.voices_path)
            return False

        try:
            log.info("Initializing Kokoro v1.0 + Misaki...")

            # Import here to avoid slow loading at startup
            from kokoro_onnx import Kokoro
            from misaki import espeak
            from misaki.espeak import EspeakG2P

            # Initialize Kokoro
            self._kokoro = Kokoro(config.model_path, config.voices_path)

            # Initialize Misaki G2P (Grapheme-to-Phoneme)
            espeak.EspeakFallback(british=False)
            self._g2p = EspeakG2P(language=config.language)

            # Load voice style
            try:
                self._voice_style = self._kokoro.get_voice_style(config.voice)
            except Exception:
                log.warning("Voice not found, using fallback", voice=config.voice, fallback="ef_dora")
                self._voice_style = self._kokoro.get_voice_style("ef_dora")

            self._ready = True
            log.info("Engine ready", voice=config.voice)
            return True

        except Exception as e:
            log.error("Initialization failed", error=str(e))
            return False

    def generate_audio(self, text: str) -> str | None:
        """
        Generate audio from text.

        Args:
            text: Text to convert to audio.

        Returns:
            Base64 encoded audio (WAV), or None on error.
        """
        if not self._ready:
            log.warning("Engine not initialized")
            return None

        if not text or not text.strip():
            return None

        try:
            # Step 1: Convert text to phonemes
            phonemes, _ = self._g2p(text)

            # Step 2: Generate audio from phonemes
            audio, sample_rate = self._kokoro.create(
                phonemes,
                voice=self._voice_style,
                speed=self._config.speed,
                is_phonemes=True,
            )

            # Step 3: Convert to WAV in memory
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format="WAV")
            buffer.seek(0)

            # Step 4: Encode to Base64
            return base64.b64encode(buffer.read()).decode("utf-8")

        except Exception as e:
            log.error("Audio generation failed", error=str(e))
            return None

    def set_voice(self, voice_name: str) -> bool:
        """
        Change the active voice.

        Args:
            voice_name: Voice name (e.g., 'ef_dora', 'em_alex')

        Returns:
            True if change was successful.
        """
        if not self._ready:
            return False

        try:
            self._voice_style = self._kokoro.get_voice_style(voice_name)
            self._config.voice = voice_name
            log.info("Voice changed", voice=voice_name)
            return True
        except Exception as e:
            log.warning("Voice not available", voice=voice_name, error=str(e))
            return False

    def set_speed(self, speed: float) -> None:
        """
        Adjust speech speed.

        Args:
            speed: Speed factor (1.0 = normal, >1 = faster)
        """
        self._config.speed = max(0.5, min(2.0, speed))
        log.info("Speed adjusted", speed=self._config.speed)


# Singleton instance
_tts_engine: TTSEngine | None = None


def get_tts_engine() -> TTSEngine:
    """Get TTS engine instance (singleton)."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
