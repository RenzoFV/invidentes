"""
Sistema de alertas sonoras para detección de obstáculos.
"""

import logging
import time
import threading
import queue
import platform
from typing import Optional, Dict
from config import (
    ALERT_ENABLED, ALERT_CLOSE_FREQUENCY, ALERT_MEDIUM_FREQUENCY, ALERT_FAR_FREQUENCY,
    ALERT_DURATION, ALERT_DEBOUNCE_TIME
)

logger = logging.getLogger(__name__)


class ObstacleAlert:
    """Sistema de alertas sonoras para obstáculos detectados."""
    
    def __init__(self):
        """Inicializa el sistema de alertas."""
        self.enabled = ALERT_ENABLED
        self.alert_queue = queue.Queue()
        self.last_alert_time = {}
        self.debounce_time = ALERT_DEBOUNCE_TIME
        self.is_playing = False
        self.alert_thread = None
        self._init_audio_system()
        self._start_alert_thread()
    
    def _init_audio_system(self):
        """Inicializa el sistema de audio según la plataforma."""
        self.system = platform.system()
        try:
            if self.system == "Windows":
                # Windows: usar winsound o pygame
                try:
                    import pygame
                    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                    self.use_pygame = True
                    logger.info("Sistema de audio inicializado con pygame")
                except ImportError:
                    self.use_pygame = False
                    logger.info("Usando winsound para alertas (Windows)")
            else:
                # Linux/Mac: usar pygame
                try:
                    import pygame
                    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                    self.use_pygame = True
                    logger.info("Sistema de audio inicializado con pygame")
                except ImportError:
                    self.use_pygame = False
                    logger.warning("pygame no disponible, alertas pueden no funcionar")
        except Exception as e:
            logger.error(f"Error al inicializar sistema de audio: {e}")
            self.use_pygame = False
    
    def _start_alert_thread(self):
        """Inicia el hilo de procesamiento de alertas."""
        self.alert_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.alert_thread.start()
    
    def _process_alerts(self):
        """Procesa la cola de alertas de forma continua."""
        while True:
            try:
                alert_data = self.alert_queue.get(timeout=1)
                if alert_data:
                    self._play_alert(alert_data)
                    self.alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando alerta: {e}")
    
    def _play_alert(self, alert_data: Dict):
        """Reproduce una alerta sonora."""
        if not self.enabled:
            return
        
        alert_type = alert_data.get('type', 'obstacle')
        frequency = alert_data.get('frequency', ALERT_MEDIUM_FREQUENCY)
        duration = alert_data.get('duration', ALERT_DURATION)
        priority = alert_data.get('priority', 'normal')
        
        # Verificar debounce
        alert_key = f"{alert_type}_{frequency}"
        current_time = time.time()
        if alert_key in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[alert_key]
            if time_since_last < self.debounce_time:
                return  # Ignorar alerta muy reciente
        
        self.last_alert_time[alert_key] = current_time
        
        try:
            if self.use_pygame:
                self._play_pygame_beep(frequency, duration)
            else:
                self._play_system_beep(frequency, duration)
        except Exception as e:
            logger.error(f"Error al reproducir alerta: {e}")
    
    def _play_pygame_beep(self, frequency: int, duration: float):
        """Reproduce un beep usando pygame."""
        try:
            import pygame
            import numpy as np
            
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            arr = np.zeros((n_samples, 2), dtype=np.int16)
            max_sample = 2**(16 - 1) - 1
            
            for i in range(n_samples):
                wave = max_sample * np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i][0] = int(wave)
                arr[i][1] = int(wave)
            
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
            pygame.time.wait(int(duration * 1000))
        except Exception as e:
            logger.error(f"Error en pygame beep: {e}")
    
    def _play_system_beep(self, frequency: int, duration: float):
        """Reproduce un beep usando el sistema."""
        try:
            if self.system == "Windows":
                import winsound
                # winsound.Beep solo acepta frecuencias entre 37-32767 Hz
                frequency = max(37, min(32767, frequency))
                winsound.Beep(frequency, int(duration * 1000))
            else:
                # Linux: usar beep command o speaker-test
                import subprocess
                try:
                    subprocess.run(['beep', '-f', str(frequency), '-l', str(int(duration * 1000))], 
                                 check=False, timeout=1)
                except:
                    # Fallback: usar speaker-test (solo genera tono, no frecuencia específica)
                    pass
        except Exception as e:
            logger.error(f"Error en system beep: {e}")
    
    def alert_obstacle(self, proximity: str, obstacle_type: str = 'unknown', priority: str = 'normal', is_center: bool = False):
        """
        Genera una alerta para un obstáculo detectado.
        SOLO suena si el objeto está cercano O en el centro (zona de peligro).
        
        Args:
            proximity: 'close', 'medium' o 'far'
            obstacle_type: Tipo de obstáculo ('person', 'vehicle', 'object', etc.)
            priority: 'high', 'normal' o 'low'
            is_center: Si está en la zona central del frame
        """
        if not self.enabled:
            return
        
        # SOLO alertar si está cercano O en el centro (zona de peligro)
        # Ignorar objetos lejanos o medios que no estén en el centro
        if proximity == 'far' and not is_center:
            return  # No hacer sonido para objetos lejanos fuera del centro
        
        if proximity == 'medium' and not is_center:
            return  # No hacer sonido para objetos medios fuera del centro
        
        # Determinar frecuencia según proximidad
        if proximity == 'close':
            frequency = ALERT_CLOSE_FREQUENCY
            duration = ALERT_DURATION * 1.5  # Más largo para cercano
        elif proximity == 'medium':
            frequency = ALERT_MEDIUM_FREQUENCY
            duration = ALERT_DURATION
        else:  # far (solo si está en el centro)
            frequency = ALERT_FAR_FREQUENCY
            duration = ALERT_DURATION * 0.5  # Muy corto para lejano en centro
        
        # Ajustar según tipo de obstáculo (variaciones menores)
        if obstacle_type == 'person':
            frequency = int(frequency * 1.1)  # Ligeramente más agudo
        elif obstacle_type in ['car', 'bus', 'truck', 'motorcycle', 'bicycle']:
            frequency = int(frequency * 0.9)  # Ligeramente más grave
        
        alert_data = {
            'type': 'obstacle',
            'frequency': frequency,
            'duration': duration,
            'proximity': proximity,
            'obstacle_type': obstacle_type,
            'priority': priority
        }
        
        try:
            self.alert_queue.put(alert_data, block=False)
        except queue.Full:
            # Si la cola está llena, ignorar (evitar acumulación)
            pass
    
    def alert_noise(self, noise_type: str, intensity: float):
        """
        Genera una alerta para ruido detectado.
        
        Args:
            noise_type: Tipo de ruido ('siren', 'traffic', 'voice', etc.)
            intensity: Intensidad del ruido (0-1)
        """
        if not self.enabled:
            return
        
        # Frecuencias específicas para tipos de ruido
        if noise_type == 'siren':
            frequency = 1200  # Tono agudo de alerta
            duration = ALERT_DURATION * 2
            priority = 'high'
        elif noise_type == 'traffic':
            frequency = 400  # Tono grave
            duration = ALERT_DURATION
            priority = 'normal'
        elif noise_type == 'voice':
            frequency = 500  # Tono medio
            duration = ALERT_DURATION * 0.8
            priority = 'low'
        else:
            frequency = ALERT_MEDIUM_FREQUENCY
            duration = ALERT_DURATION
            priority = 'normal'
        
        alert_data = {
            'type': 'noise',
            'frequency': frequency,
            'duration': duration,
            'noise_type': noise_type,
            'intensity': intensity,
            'priority': priority
        }
        
        try:
            self.alert_queue.put(alert_data, block=False)
        except queue.Full:
            pass
    
    def set_enabled(self, enabled: bool):
        """Habilita o deshabilita las alertas."""
        self.enabled = enabled
        if not enabled:
            # Limpiar cola
            while not self.alert_queue.empty():
                try:
                    self.alert_queue.get_nowait()
                except queue.Empty:
                    break
    
    def stop(self):
        """Detiene el sistema de alertas."""
        self.set_enabled(False)
        if self.use_pygame:
            try:
                import pygame
                pygame.mixer.quit()
            except:
                pass



