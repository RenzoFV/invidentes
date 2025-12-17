"""
Módulo para detectar ruido y sonidos en el entorno.
"""

import logging
import numpy as np
import pyaudio
import time
from typing import Dict, Optional
from config import AUDIO_SAMPLE_RATE, AUDIO_CHUNK_SIZE, NOISE_THRESHOLD

logger = logging.getLogger(__name__)


class AudioDetector:
    """Detector de ruido y sonidos ambientales."""
    
    def __init__(self):
        """Inicializa el detector de audio."""
        self.audio = None
        self.stream = None
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.chunk_size = AUDIO_CHUNK_SIZE
        self.noise_threshold = NOISE_THRESHOLD
        self.is_listening = False
        
    def start_listening(self):
        """Inicia la captura de audio."""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            self.is_listening = True
            logger.info("Detector de audio iniciado")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar detector de audio: {e}")
            return False
    
    def stop_listening(self):
        """Detiene la captura de audio."""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
            self.is_listening = False
            logger.info("Detector de audio detenido")
        except Exception as e:
            logger.error(f"Error al detener detector de audio: {e}")
    
    def detect_noise(self) -> Optional[Dict]:
        """
        Detecta ruido en el audio capturado.
        
        Returns:
            Diccionario con información del ruido detectado o None si no hay ruido significativo
        """
        if not self.is_listening or not self.stream:
            return None
        
        try:
            # Leer datos de audio
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Convertir a array numpy
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calcular nivel de ruido (RMS - Root Mean Square)
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Normalizar a escala 0-1
            max_value = 32768.0  # Valor máximo para int16
            normalized_rms = rms / max_value
            
            # Determinar si hay ruido significativo
            if normalized_rms > self.noise_threshold:
                # Clasificar nivel de ruido
                if normalized_rms > 0.7:
                    level = "muy alto"
                elif normalized_rms > 0.5:
                    level = "alto"
                elif normalized_rms > 0.3:
                    level = "moderado"
                else:
                    level = "bajo"
                
                return {
                    'has_noise': True,
                    'level': level,
                    'intensity': float(normalized_rms),
                    'description': f"Se detecta ruido {level} en el entorno"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error al detectar ruido: {e}")
            return None
    
    def get_audio_level(self) -> float:
        """
        Obtiene el nivel de audio actual sin clasificar.
        
        Returns:
            Nivel de audio normalizado (0-1)
        """
        if not self.is_listening or not self.stream:
            return 0.0
        
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data**2))
            return min(rms / 32768.0, 1.0)
        except:
            return 0.0

