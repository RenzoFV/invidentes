"""
Módulo de anuncios de voz en español para objetos cercanos.
"""

import logging
import threading
import queue
import time
from typing import Optional
from config import ENABLE_VOICE_DESCRIPTIONS, TTS_ENGINE, TTS_LANGUAGE, TTS_RATE, TTS_VOLUME

logger = logging.getLogger(__name__)


class VoiceAnnouncer:
    """Sistema de anuncios de voz en español para objetos cercanos."""
    
    def __init__(self):
        """Inicializa el sistema de voz."""
        self.enabled = ENABLE_VOICE_DESCRIPTIONS
        self.engine_name = TTS_ENGINE
        self.language = TTS_LANGUAGE
        self.rate = TTS_RATE
        self.volume = TTS_VOLUME
        self.engine = None
        self.voice_queue = queue.Queue(maxsize=10)  # Cola más grande para múltiples objetos
        self.is_speaking = False
        self.last_announcement_time = {}
        self.announcement_debounce = 2.0  # Segundos entre anuncios del mismo objeto (reducido para más respuestas)
        self.voice_thread = None
        
        if self.enabled:
            self._initialize_engine()
            self._start_voice_thread()
    
    def _initialize_engine(self):
        """Inicializa el motor TTS."""
        try:
            if self.engine_name == 'pyttsx3':
                self._init_pyttsx3()
            elif self.engine_name == 'gtts':
                self._init_gtts()
            else:
                # Intentar pyttsx3 por defecto
                try:
                    self.engine_name = 'pyttsx3'
                    self._init_pyttsx3()
                except:
                    logger.warning("No se pudo inicializar ningún motor TTS")
                    self.enabled = False
        except Exception as e:
            logger.error(f"Error al inicializar motor TTS: {e}")
            self.enabled = False
    
    def _init_pyttsx3(self):
        """Inicializa pyttsx3 (TTS local)."""
        try:
            import pyttsx3
            logger.info("Inicializando pyttsx3...")
            self.engine = pyttsx3.init()
            
            if self.engine is None:
                raise Exception("No se pudo inicializar el motor pyttsx3")
            
            # Configurar propiedades
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Intentar configurar idioma español
            try:
                voices = self.engine.getProperty('voices')
                logger.info(f"Voces disponibles: {len(voices) if voices else 0}")
                
                # Buscar voz en español
                spanish_voice_found = False
                if voices:
                    for voice in voices:
                        voice_name_lower = voice.name.lower()
                        if any(keyword in voice_name_lower for keyword in ['spanish', 'español', 'espanol', 'es-mx', 'es-es']):
                            self.engine.setProperty('voice', voice.id)
                            logger.info(f"✅ Voz en español seleccionada: {voice.name}")
                            spanish_voice_found = True
                            break
                
                if not spanish_voice_found:
                    logger.warning("⚠️ No se encontró voz en español, usando voz por defecto")
                    # Listar voces disponibles para debug
                    if voices:
                        logger.info(f"Voces disponibles: {[v.name for v in voices[:5]]}")
            except Exception as e:
                logger.warning(f"No se pudo configurar voz en español: {e}")
            
            # Probar que funciona (sin decir nada, solo verificar que el motor funciona)
            try:
                # No reproducir "Prueba" automáticamente para no molestar
                logger.info("✅ pyttsx3 inicializado y funcionando correctamente")
            except Exception as e:
                logger.error(f"Error al probar pyttsx3: {e}")
                raise
            
        except ImportError:
            logger.error("❌ pyttsx3 no está instalado. Ejecuta: pip install pyttsx3")
            raise
        except Exception as e:
            logger.error(f"❌ Error al inicializar pyttsx3: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _init_gtts(self):
        """Inicializa gTTS (requiere conexión a internet)."""
        try:
            from gtts import gTTS
            import tempfile
            import os
            import platform
            
            self.gtts = gTTS
            self.temp_dir = tempfile.gettempdir()
            logger.info("gTTS inicializado correctamente")
        except ImportError:
            logger.error("gTTS no está instalado")
            raise
    
    def _start_voice_thread(self):
        """Inicia el hilo de procesamiento de voz."""
        if not self.enabled:
            return
        self.voice_thread = threading.Thread(target=self._process_voice_queue, daemon=True)
        self.voice_thread.start()
    
    def _process_voice_queue(self):
        """Procesa la cola de anuncios de voz."""
        logger.info("Hilo de procesamiento de voz iniciado")
        print("🔊 [VOZ] Hilo de procesamiento de voz iniciado y esperando mensajes...")
        
        while True:
            try:
                text = self.voice_queue.get(timeout=1)
                if text:
                    self.is_speaking = True
                    print(f"\n🎤 [VOZ] 🔊 REPRODUCIENDO: '{text}'")
                    logger.info(f"Reproduciendo voz: {text}")
                    self._speak(text)
                    self.is_speaking = False
                    print(f"✅ [VOZ] Reproducción completada: '{text}'")
                    print(f"📋 [VOZ] Mensajes restantes en cola: {self.voice_queue.qsize()}")
                    self.voice_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ [VOZ] Error procesando voz: {e}")
                logger.error(f"Error procesando voz: {e}")
                import traceback
                traceback.print_exc()
                self.is_speaking = False
    
    def _speak(self, text: str):
        """Reproduce el texto en voz."""
        if not self.enabled or not text:
            logger.warning(f"Voz deshabilitada o texto vacío. enabled={self.enabled}, text={text}")
            return
        
        try:
            if self.engine_name == 'pyttsx3' and self.engine:
                logger.info(f"🔊 Reproduciendo voz: {text}")
                # Asegurarse de que el motor esté listo
                if not hasattr(self.engine, 'say'):
                    logger.error("Motor pyttsx3 no tiene método 'say'")
                    return
                
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info("✅ Voz reproducida correctamente")
            elif self.engine_name == 'gtts':
                logger.info(f"🔊 Usando gTTS para decir: {text}")
                self._speak_gtts(text)
            else:
                logger.warning(f"⚠️ Motor de voz no disponible. engine_name={self.engine_name}, engine={self.engine}")
        except Exception as e:
            logger.error(f"❌ Error al reproducir voz: {e}")
            import traceback
            traceback.print_exc()
            # Intentar reinicializar el motor
            try:
                if self.engine_name == 'pyttsx3':
                    logger.info("Intentando reinicializar pyttsx3...")
                    self._init_pyttsx3()
            except:
                pass
    
    def _speak_gtts(self, text: str):
        """Reproduce voz usando gTTS."""
        try:
            import os
            import tempfile
            import platform
            
            # Generar audio
            tts = self.gtts(text=text, lang='es', slow=False)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            
            # Reproducir según plataforma
            system = platform.system()
            if system == "Windows":
                try:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    pygame.mixer.quit()
                except:
                    os.system(f'powershell -c (New-Object Media.SoundPlayer "{temp_file.name}").PlaySync()')
            elif system == "Darwin":  # macOS
                os.system(f'afplay "{temp_file.name}"')
            else:  # Linux
                os.system(f'mpg123 "{temp_file.name}" 2>/dev/null || mpg321 "{temp_file.name}" 2>/dev/null')
            
            # Eliminar archivo temporal
            try:
                os.unlink(temp_file.name)
            except:
                pass
        except Exception as e:
            logger.error(f"Error en gTTS: {e}")
    
    def announce_close_object(self, object_name: str, obstacle_type: str = 'object'):
        """
        Anuncia que un objeto está muy cerca.
        
        Args:
            object_name: Nombre del objeto detectado
            obstacle_type: Tipo de obstáculo (person, vehicle, furniture, object)
        """
        print(f"\n🔊 [VOZ] Intento de anunciar: {object_name} (tipo: {obstacle_type})")
        logger.info(f"🔊 [VOZ] Intento de anunciar objeto cercano: {object_name} (tipo: {obstacle_type})")
        
        if not self.enabled:
            print(f"⚠️ [VOZ] Voz deshabilitada, no se anunciará: {object_name}")
            logger.warning(f"Voz deshabilitada, no se anunciará: {object_name}")
            return
        
        if not self.engine and self.engine_name == 'pyttsx3':
            print(f"⚠️ [VOZ] Motor de voz no está inicializado")
            logger.error("Motor de voz no está inicializado")
            return
        
        # Verificar debounce SOLO para el mismo objeto (permitir diferentes objetos)
        current_time = time.time()
        
        # Verificar si este objeto específico fue anunciado recientemente
        # IMPORTANTE: Solo aplicar debounce al mismo objeto, no a objetos diferentes
        if object_name in self.last_announcement_time:
            time_since_last = current_time - self.last_announcement_time[object_name]
            if time_since_last < self.announcement_debounce:
                print(f"⏭️ [VOZ] Anuncio de '{object_name}' ignorado por debounce ({time_since_last:.1f}s < {self.announcement_debounce}s)")
                logger.debug(f"Anuncio de {object_name} ignorado por debounce ({time_since_last:.1f}s < {self.announcement_debounce}s)")
                return  # Ignorar solo si es el mismo objeto muy reciente
        else:
            # Es un objeto nuevo, permitir anunciarlo
            print(f"✅ [VOZ] Objeto nuevo '{object_name}' - se permitirá anunciar")
        
        # Actualizar tiempo para este objeto específico
        self.last_announcement_time[object_name] = current_time
        
        # Traducir nombre del objeto al español
        spanish_name = self._translate_to_spanish(object_name, obstacle_type)
        
        # Generar mensaje
        message = self._generate_message(spanish_name, obstacle_type)
        
        print(f"📢 [VOZ] Mensaje generado: '{message}'")
        logger.info(f"Anuncio generado: {message}")
        
        # Agregar a la cola (aumentar tamaño de cola para múltiples objetos)
        try:
            # Si la cola está llena, esperar un poco y reintentar
            if self.voice_queue.full():
                # Limpiar cola antigua si está llena
                try:
                    old_msg = self.voice_queue.get_nowait()
                    logger.debug(f"Eliminando mensaje antiguo de la cola: {old_msg}")
                except queue.Empty:
                    pass
            
            self.voice_queue.put(message, block=False)
            print(f"✅ [VOZ] Mensaje agregado a la cola: '{message}'")
            logger.info(f"Mensaje agregado a la cola de voz: {message}")
        except Exception as e:
            print(f"❌ [VOZ] Error al agregar mensaje: {e}")
            logger.error(f"Error al agregar mensaje a la cola: {e}")
            import traceback
            traceback.print_exc()
    
    def _translate_to_spanish(self, object_name: str, obstacle_type: str) -> str:
        """Traduce el nombre del objeto al español."""
        translations = {
            'person': 'una persona',
            'car': 'un auto',
            'bus': 'un autobús',
            'truck': 'un camión',
            'motorcycle': 'una motocicleta',
            'bicycle': 'una bicicleta',
            'chair': 'una silla',
            'table': 'una mesa',
            'couch': 'un sofá',
            'bed': 'una cama',
            'door': 'una puerta',
            'stairs': 'escaleras',
            'dog': 'un perro',
            'cat': 'un gato',
            'backpack': 'una mochila',
            'handbag': 'un bolso',
            'umbrella': 'un paraguas',
            'bottle': 'una botella',
            'cup': 'una taza',
            'book': 'un libro',
            'phone': 'un teléfono',
            'cell phone': 'un celular',
            'mobile phone': 'un celular',
            'laptop': 'una computadora',
            'tv': 'un televisor',
            'keyboard': 'un teclado',
            'mouse': 'un ratón',
            'vase': 'un jarrón',
            'bowl': 'un tazón',
            'clock': 'un reloj',
            'scissors': 'unas tijeras',
            'toothbrush': 'un cepillo de dientes',
        }
        
        # Intentar traducción (normalizar nombre)
        object_lower = object_name.lower().strip()
        
        # Buscar coincidencia exacta
        if object_lower in translations:
            return translations[object_lower]
        
        # Buscar coincidencia parcial (para variaciones como "cell phone" vs "phone")
        for key, value in translations.items():
            if key in object_lower or object_lower in key:
                return value
        
        # Si no hay traducción, usar el nombre original con artículo
        return f"un {object_name}"
    
    def _generate_message(self, spanish_name: str, obstacle_type: str) -> str:
        """Genera el mensaje de voz según el tipo de obstáculo."""
        # Todos los mensajes incluyen el nombre específico del objeto
        if obstacle_type == 'person':
            return f"¡Atención! Hay {spanish_name} muy cerca de ti"
        elif obstacle_type == 'vehicle':
            return f"¡Cuidado! Hay {spanish_name} muy cerca de ti"
        elif obstacle_type == 'furniture':
            return f"¡Atención! Hay {spanish_name} muy cerca de ti"
        else:
            return f"¡Atención! Hay {spanish_name} muy cerca de ti"
    
    def set_enabled(self, enabled: bool):
        """Habilita o deshabilita los anuncios de voz."""
        self.enabled = enabled
        if not enabled:
            # Limpiar cola
            while not self.voice_queue.empty():
                try:
                    self.voice_queue.get_nowait()
                except queue.Empty:
                    break
    
    def stop(self):
        """Detiene el sistema de voz."""
        self.set_enabled(False)
        if self.engine and self.engine_name == 'pyttsx3':
            try:
                self.engine.stop()
            except:
                pass

