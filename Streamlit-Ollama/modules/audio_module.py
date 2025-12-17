"""
Módulo de síntesis de voz (TTS) con soporte para múltiples motores.
"""

import logging
import queue
import threading
import hashlib
import os
from typing import Optional
from config import (
    TTS_ENGINE, TTS_LANGUAGE, TTS_RATE, TTS_VOLUME,
    AUDIO_QUEUE_MAX_SIZE
)

logger = logging.getLogger(__name__)


class AudioManager:
    """Gestor de síntesis de voz con cola para evitar solapamientos."""
    
    def __init__(self, engine: str = None, language: str = None):
        """
        Inicializa el gestor de audio.
        
        Args:
            engine: Motor TTS a usar ('gtts' o 'pyttsx3')
            language: Idioma para TTS
        """
        self.engine_name = engine or TTS_ENGINE
        self.language = language or TTS_LANGUAGE
        self.volume = TTS_VOLUME
        self.rate = TTS_RATE
        self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAX_SIZE)
        self.is_playing = False
        self.audio_cache_dir = "audio_cache"
        self._initialize_engine()
        self._start_audio_thread()
    
    def _initialize_engine(self):
        """Inicializa el motor TTS seleccionado."""
        try:
            if self.engine_name == 'gtts':
                self._init_gtts()
            elif self.engine_name == 'pyttsx3':
                self._init_pyttsx3()
            else:
                logger.warning(f"Motor '{self.engine_name}' no reconocido, usando gTTS")
                self._init_gtts()
        except Exception as e:
            logger.error(f"Error al inicializar motor TTS: {e}")
            # Fallback a pyttsx3
            try:
                self.engine_name = 'pyttsx3'
                self._init_pyttsx3()
            except Exception as e2:
                logger.error(f"Error al inicializar fallback: {e2}")
    
    def _init_gtts(self):
        """Inicializa Google Text-to-Speech."""
        try:
            from gtts import gTTS
            import tempfile
            self.gtts = gTTS
            self.temp_dir = tempfile.gettempdir()
            logger.info("gTTS inicializado correctamente")
        except ImportError:
            logger.error("gTTS no está instalado")
            raise
    
    def _init_pyttsx3(self):
        """Inicializa pyttsx3 (TTS local)."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configurar propiedades
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Intentar configurar idioma (si está disponible)
            try:
                voices = self.engine.getProperty('voices')
                # Buscar voz en español
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            except:
                pass
            
            logger.info("pyttsx3 inicializado correctamente")
        except ImportError:
            logger.error("pyttsx3 no está instalado")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar pyttsx3: {e}")
            raise
    
    def _start_audio_thread(self):
        """Inicia el hilo de procesamiento de audio."""
        self.audio_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.audio_thread.start()
    
    def _process_audio_queue(self):
        """Procesa la cola de audio de forma continua."""
        while True:
            try:
                text = self.audio_queue.get(timeout=1)
                if text:
                    self.is_playing = True
                    self._speak_sync(text)
                    self.is_playing = False
                    self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en procesamiento de audio: {e}")
                self.is_playing = False
    
    def _speak_sync(self, text: str):
        """
        Reproduce audio de forma síncrona.
        
        Args:
            text: Texto a convertir en audio
        """
        try:
            if self.engine_name == 'gtts':
                self._speak_gtts(text)
            elif self.engine_name == 'pyttsx3':
                self._speak_pyttsx3(text)
        except Exception as e:
            logger.error(f"Error al reproducir audio: {e}")
    
    def _speak_gtts(self, text: str):
        """Reproduce audio usando gTTS."""
        try:
            # Crear directorio de cache si no existe
            if not os.path.exists(self.audio_cache_dir):
                os.makedirs(self.audio_cache_dir)
            
            # Generar hash del texto para cache
            text_hash = hashlib.md5(text.encode()).hexdigest()
            audio_file = os.path.join(self.audio_cache_dir, f"{text_hash}.mp3")
            
            # Verificar si existe en cache
            if os.path.exists(audio_file):
                self._play_audio_file(audio_file)
                return
            
            # Generar audio
            tts = self.gtts(text=text, lang=self.language, slow=False)
            tts.save(audio_file)
            
            # Reproducir
            self._play_audio_file(audio_file)
            
        except Exception as e:
            logger.error(f"Error en gTTS: {e}")
            # Fallback a pyttsx3 si está disponible
            if hasattr(self, 'engine'):
                self._speak_pyttsx3(text)
    
    def _speak_pyttsx3(self, text: str):
        """Reproduce audio usando pyttsx3."""
        try:
            if not hasattr(self, 'engine'):
                self._init_pyttsx3()
            
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error en pyttsx3: {e}")
    
    def _play_audio_file(self, file_path: str):
        """Reproduce un archivo de audio."""
        try:
            import platform
            system = platform.system()
            
            # Obtener ruta absoluta (mejor compatibilidad multiplataforma)
            abs_path = os.path.abspath(file_path)
            
            if system == "Windows":
                # En Windows, usar pygame para mejor compatibilidad
                try:
                    import pygame
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                    pygame.mixer.music.load(abs_path)
                    pygame.mixer.music.play()
                    # Esperar a que termine la reproducción
                    while pygame.mixer.music.get_busy():
                        import time
                        time.sleep(0.1)
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    return
                except ImportError:
                    logger.warning("pygame no disponible, usando fallback")
                    # Fallback: usar PowerShell para reproducir MP3
                    try:
                        escaped_path = abs_path.replace('"', '\\"')
                        os.system(f'powershell -c (New-Object Media.SoundPlayer "{escaped_path}").PlaySync()')
                        return
                    except Exception as ps_error:
                        logger.error(f"Error con PowerShell: {ps_error}")
                except Exception as pygame_error:
                    logger.error(f"Error con pygame: {pygame_error}")
                    # Fallback a PowerShell
                    try:
                        escaped_path = abs_path.replace('"', '\\"')
                        os.system(f'powershell -c (New-Object Media.SoundPlayer "{escaped_path}").PlaySync()')
                        return
                    except:
                        pass
            elif system == "Darwin":  # macOS
                os.system(f'afplay "{abs_path}"')
            else:  # Linux
                os.system(f'aplay "{abs_path}" 2>/dev/null || mpg123 "{abs_path}" 2>/dev/null || mpv "{abs_path}" 2>/dev/null')
        except Exception as e:
            logger.error(f"Error al reproducir archivo de audio: {e}")
            # Último fallback: intentar con pyttsx3 si está disponible
            try:
                if hasattr(self, 'engine'):
                    # Leer el texto del archivo y usar pyttsx3
                    logger.warning("Usando fallback de audio")
            except:
                pass
    
    def speak(self, text: str, priority: bool = False):
        """
        Añade texto a la cola de audio para reproducción.
        
        Args:
            text: Texto a convertir en audio
            priority: Si es True, añade al frente de la cola
        """
        if not text or not text.strip():
            return
        
        try:
            if priority:
                # Para prioridad, vaciamos la cola y añadimos el nuevo
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
            
            if self.audio_queue.full():
                # Si la cola está llena, eliminamos el más antiguo
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.audio_queue.put(text)
            logger.debug(f"Texto añadido a cola de audio: {text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error al añadir texto a cola: {e}")
    
    def set_volume(self, volume: float):
        """
        Establece el volumen de audio.
        
        Args:
            volume: Volumen entre 0.0 y 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        if hasattr(self, 'engine'):
            try:
                self.engine.setProperty('volume', self.volume)
            except:
                pass
        logger.info(f"Volumen establecido a {self.volume}")
    
    def set_rate(self, rate: int):
        """
        Establece la velocidad de habla.
        
        Args:
            rate: Velocidad en palabras por minuto
        """
        self.rate = max(50, min(300, rate))
        if hasattr(self, 'engine'):
            try:
                self.engine.setProperty('rate', self.rate)
            except:
                pass
        logger.info(f"Velocidad establecida a {self.rate}")
    
    def stop(self):
        """Detiene la reproducción actual y limpia la cola."""
        try:
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            logger.info("Cola de audio limpiada")
        except Exception as e:
            logger.error(f"Error al detener audio: {e}")
    
    def is_busy(self) -> bool:
        """Verifica si hay audio reproduciéndose o en cola."""
        return self.is_playing or not self.audio_queue.empty()

