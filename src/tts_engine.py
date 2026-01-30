"""
TAMARA TTS Engine Module
Text-to-speech engine using Kokoro + Misaki.
"""

import base64
import io
import os
from typing import Optional

import numpy as np
import soundfile as sf

from .config import get_config


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
        self._config = get_config().tts
    
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
            print(f"[TTS] ERROR: Model not found: {config.model_path}")
            return False
        
        if not os.path.exists(config.voices_path):
            print(f"[TTS] ERROR: Voices not found: {config.voices_path}")
            return False
        
        try:
            print("[TTS] Initializing Kokoro v1.0 + Misaki...")
            
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
                print(f"[TTS] Voice '{config.voice}' not found, using 'ef_dora'")
                self._voice_style = self._kokoro.get_voice_style('ef_dora')
            
            self._ready = True
            print(f"[TTS] Engine ready! Voice: {config.voice}")
            return True
            
        except Exception as e:
            print(f"[TTS] Initialization ERROR: {e}")
            return False
    
    def generate_audio(self, text: str) -> Optional[str]:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to audio.
            
        Returns:
            Base64 encoded audio (WAV), or None on error.
        """
        if not self._ready:
            print("[TTS] Engine not initialized")
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
                is_phonemes=True
            )
            
            # Step 3: Convert to WAV in memory
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format='WAV')
            buffer.seek(0)
            
            # Step 4: Encode to Base64
            return base64.b64encode(buffer.read()).decode('utf-8')
            
        except Exception as e:
            print(f"[TTS] Error generating audio: {e}")
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
            print(f"[TTS] Voice changed to: {voice_name}")
            return True
        except Exception as e:
            print(f"[TTS] Voice '{voice_name}' not available: {e}")
            return False
    
    def set_speed(self, speed: float) -> None:
        """
        Adjust speech speed.
        
        Args:
            speed: Speed factor (1.0 = normal, >1 = faster)
        """
        self._config.speed = max(0.5, min(2.0, speed))
        print(f"[TTS] Speed adjusted to: {self._config.speed}")


# Singleton instance
_tts_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """Get TTS engine instance (singleton)."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
