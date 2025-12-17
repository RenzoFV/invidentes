"""
Módulo avanzado para detectar ruido y sonidos en el entorno.
"""

import logging
import numpy as np
import pyaudio
import time
from typing import Dict, Optional
from config import (
    AUDIO_SAMPLE_RATE, AUDIO_CHUNK_SIZE, NOISE_THRESHOLD,
    SIREN_FREQ_MIN, SIREN_FREQ_MAX, TRAFFIC_FREQ_MIN, TRAFFIC_FREQ_MAX
)

logger = logging.getLogger(__name__)


class AudioDetector:
    """Detector avanzado de ruido y sonidos ambientales con análisis de frecuencia."""
    
    def __init__(self):
        """Inicializa el detector de audio."""
        self.audio = None
        self.stream = None
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.chunk_size = AUDIO_CHUNK_SIZE
        self.noise_threshold = NOISE_THRESHOLD
        self.is_listening = False
        self.fft_enabled = True
        
        # Intentar importar scipy para análisis de frecuencia
        try:
            from scipy import signal
            self.has_scipy = True
        except ImportError:
            logger.warning("scipy no disponible, análisis de frecuencia limitado")
            self.has_scipy = False
    
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
    
    def _analyze_frequencies(self, audio_data: np.ndarray) -> Dict:
        """
        Analiza las frecuencias dominantes en el audio.
        
        Args:
            audio_data: Array de datos de audio
            
        Returns:
            Diccionario con información de frecuencias
        """
        if not self.has_scipy or len(audio_data) < 2:
            return {'dominant_freq': 0, 'freq_bands': {}}
        
        try:
            # Calcular FFT
            fft = np.fft.fft(audio_data)
            fft_freq = np.fft.fftfreq(len(audio_data), 1.0 / self.sample_rate)
            
            # Solo frecuencias positivas
            positive_freq_idx = fft_freq > 0
            fft_freq = fft_freq[positive_freq_idx]
            fft_magnitude = np.abs(fft[positive_freq_idx])
            
            # Encontrar frecuencia dominante
            dominant_idx = np.argmax(fft_magnitude)
            dominant_freq = fft_freq[dominant_idx]
            
            # Analizar bandas de frecuencia
            freq_bands = {
                'low': np.sum(fft_magnitude[(fft_freq >= TRAFFIC_FREQ_MIN) & (fft_freq <= TRAFFIC_FREQ_MAX)]),
                'mid': np.sum(fft_magnitude[(fft_freq > TRAFFIC_FREQ_MAX) & (fft_freq < SIREN_FREQ_MIN)]),
                'high': np.sum(fft_magnitude[(fft_freq >= SIREN_FREQ_MIN) & (fft_freq <= SIREN_FREQ_MAX)])
            }
            
            return {
                'dominant_freq': float(dominant_freq),
                'freq_bands': {k: float(v) for k, v in freq_bands.items()}
            }
        except Exception as e:
            logger.error(f"Error en análisis de frecuencia: {e}")
            return {'dominant_freq': 0, 'freq_bands': {}}
    
    def _classify_noise_type(self, freq_info: Dict, intensity: float) -> Optional[str]:
        """
        Clasifica el tipo de ruido basado en análisis de frecuencia.
        
        Args:
            freq_info: Información de frecuencias
            intensity: Intensidad del ruido
            
        Returns:
            Tipo de ruido detectado o None
        """
        if intensity < self.noise_threshold:
            return None
        
        dominant_freq = freq_info.get('dominant_freq', 0)
        freq_bands = freq_info.get('freq_bands', {})
        
        # Detectar sirenas (frecuencias altas características)
        high_band = freq_bands.get('high', 0)
        if dominant_freq >= SIREN_FREQ_MIN and dominant_freq <= SIREN_FREQ_MAX:
            if high_band > freq_bands.get('low', 0) * 2:  # Alta frecuencia dominante
                return 'siren'
        
        # Detectar tráfico (frecuencias bajas)
        low_band = freq_bands.get('low', 0)
        if dominant_freq >= TRAFFIC_FREQ_MIN and dominant_freq <= TRAFFIC_FREQ_MAX:
            if low_band > freq_bands.get('mid', 0) * 1.5:  # Baja frecuencia dominante
                return 'traffic'
        
        # Detectar voces (frecuencias medias, 300-3000 Hz)
        mid_band = freq_bands.get('mid', 0)
        if 300 <= dominant_freq <= 3000:
            if mid_band > low_band and mid_band > high_band * 0.5:
                return 'voice'
        
        # Ruido general
        return 'general'
    
    def detect_noise(self) -> Optional[Dict]:
        """
        Detecta y clasifica ruido en el audio capturado.
        
        Returns:
            Diccionario con información del ruido detectado o None
        """
        if not self.is_listening or not self.stream:
            return None
        
        try:
            # Leer datos de audio
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Convertir a array numpy
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            # Normalizar
            audio_data = audio_data / 32768.0
            
            # Calcular nivel de ruido (RMS)
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Determinar si hay ruido significativo
            if rms > self.noise_threshold:
                # Analizar frecuencias
                audio_int16 = (audio_data * 32768.0).astype(np.int16)
                freq_info = self._analyze_frequencies(audio_int16)
                
                # Clasificar tipo de ruido
                noise_type = self._classify_noise_type(freq_info, rms)
                
                # Clasificar nivel de ruido
                if rms > 0.7:
                    level = "muy alto"
                elif rms > 0.5:
                    level = "alto"
                elif rms > 0.3:
                    level = "moderado"
                else:
                    level = "bajo"
                
                return {
                    'has_noise': True,
                    'level': level,
                    'intensity': float(rms),
                    'noise_type': noise_type or 'general',
                    'dominant_frequency': freq_info.get('dominant_freq', 0),
                    'description': f"Se detecta ruido {level} ({noise_type or 'general'}) en el entorno"
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
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0
            rms = np.sqrt(np.mean(audio_data**2))
            return min(float(rms), 1.0)
        except:
            return 0.0

