"""
Aplicación principal para asistente virtual de detección de obstáculos en tiempo real.
"""

import cv2
import numpy as np
import logging
import time
import threading
import queue
from typing import Optional
from config import (
    CAMERA_INDEX, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, SHOW_VIDEO_WINDOW,
    OBSTACLE_DETECTION_ENABLED, ENABLE_AUDIO_DETECTION, ENABLE_VOICE_DESCRIPTIONS,
    OPERATION_MODE, SENSITIVITY, ENABLE_GUI
)
from agents.vision_agent import VisionAgent
from modules.obstacle_alert import ObstacleAlert
from modules.audio_detector import AudioDetector
from modules.voice_announcer import VoiceAnnouncer
from utils.helpers import validate_camera_access
from config import LOG_LEVEL, LOG_FILE, ENABLE_GUI
from gui.obstacle_gui import ObstacleGUI

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ObstacleAssistant:
    """Aplicación principal para detección de obstáculos en tiempo real."""
    
    def __init__(self):
        """Inicializa el asistente."""
        self.running = False
        self.cap = None
        self.vision_agent = None
        self.obstacle_alert = None
        self.audio_detector = None
        self.voice_announcer = None
        
        # Threading
        self.video_thread = None
        self.detection_thread = None
        self.audio_thread = None
        
        # Queues para comunicación entre threads
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=10)  # Cola para GUI
        self.current_detections = []  # Detecciones actuales para dibujar en video
        self.detections_lock = threading.Lock()  # Lock para acceso thread-safe
        
        # GUI
        self.gui = None
        self.gui_thread = None
        
        # Estado
        self.last_detection_time = 0
        self.last_audio_check_time = 0
        
        # Inicializar componentes
        self._initialize_components()
        
        # Inicializar GUI si está habilitada
        if ENABLE_GUI:
            self._initialize_gui()
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema."""
        try:
            # Validar cámara
            camera_ok, camera_msg = validate_camera_access(CAMERA_INDEX)
            if not camera_ok:
                logger.error(f"Error de cámara: {camera_msg}")
                raise Exception(f"No se puede acceder a la cámara: {camera_msg}")
            
            logger.info("Cámara validada correctamente")
            
            # Inicializar agente de visión
            if OBSTACLE_DETECTION_ENABLED:
                self.vision_agent = VisionAgent()
                logger.info("Agente de visión inicializado")
            
            # Inicializar sistema de alertas
            self.obstacle_alert = ObstacleAlert()
            logger.info("Sistema de alertas inicializado")
            
            # Inicializar sistema de voz
            print("🔊 Inicializando sistema de voz...")
            self.voice_announcer = VoiceAnnouncer()
            if self.voice_announcer.enabled:
                print("✅ Sistema de voz inicializado y habilitado")
                logger.info("Sistema de voz inicializado y habilitado")
                # Verificar que el motor funciona (sin reproducir para no molestar)
                if self.voice_announcer.engine:
                    print("✅ Motor de voz listo y funcionando")
                else:
                    print("⚠️ Motor de voz no disponible")
            else:
                print("⚠️ Sistema de voz deshabilitado o no disponible")
                logger.warning("Sistema de voz deshabilitado o no disponible")
            
            # Inicializar detector de audio
            if ENABLE_AUDIO_DETECTION:
                self.audio_detector = AudioDetector()
                if self.audio_detector.start_listening():
                    logger.info("Detector de audio inicializado")
                else:
                    logger.warning("No se pudo inicializar detector de audio")
                    self.audio_detector = None
            
            logger.info("Todos los componentes inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes: {e}")
            raise
    
    def _initialize_gui(self):
        """Inicializa la interfaz gráfica."""
        try:
            self.gui = ObstacleGUI(self.detection_queue)
            logger.info("Interfaz gráfica inicializada")
        except Exception as e:
            logger.error(f"Error al inicializar GUI: {e}")
            self.gui = None
    
    def _video_capture_thread(self):
        """Hilo para captura continua de video."""
        logger.info("Hilo de captura de video iniciado")
        
        try:
            # Abrir cámara
            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0)
            
            if not self.cap.isOpened():
                logger.error("No se pudo abrir la cámara")
                return
            
            # Configurar propiedades
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reducir buffer para menor latencia
            
            frame_count = 0
            
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    logger.warning("No se pudo leer frame de la cámara")
                    time.sleep(0.1)
                    continue
                
                # Mostrar video si está habilitado
                if SHOW_VIDEO_WINDOW:
                    # Dibujar información en el frame
                    display_frame = frame.copy()
                    
                    # Obtener detecciones actuales (thread-safe)
                    with self.detections_lock:
                        current_detections = self.current_detections.copy()
                    
                    # Dibujar bounding boxes y etiquetas
                    for detection in current_detections:
                        bbox = detection.get('bbox', {})
                        x1 = int(bbox.get('x1', 0))
                        y1 = int(bbox.get('y1', 0))
                        x2 = int(bbox.get('x2', 0))
                        y2 = int(bbox.get('y2', 0))
                        name = detection.get('name', 'Unknown')
                        confidence = detection.get('confidence', 0)
                        proximity = detection.get('proximity', 'far')
                        is_center = detection.get('is_center', False)
                        
                        # Color según proximidad
                        if proximity == 'close':
                            color = (0, 0, 255)  # Rojo
                            thickness = 3
                        elif proximity == 'medium':
                            color = (0, 165, 255)  # Naranja
                            thickness = 2
                        else:
                            color = (0, 255, 0)  # Verde
                            thickness = 2
                        
                        # Dibujar rectángulo
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
                        
                        # Texto con nombre y confianza
                        label = f"{name} {confidence:.0%}"
                        if is_center:
                            label += " [CENTRO]"
                        
                        # Tamaño del texto
                        font_scale = 0.6
                        font_thickness = 2
                        (text_width, text_height), baseline = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
                        )
                        
                        # Fondo para el texto
                        cv2.rectangle(
                            display_frame,
                            (x1, y1 - text_height - 10),
                            (x1 + text_width, y1),
                            color,
                            -1
                        )
                        
                        # Texto
                        cv2.putText(
                            display_frame,
                            label,
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            font_scale,
                            (255, 255, 255),
                            font_thickness
                        )
                    
                    # Información general
                    cv2.putText(display_frame, "Obstacle Assistant - Running", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    fps_text = f"FPS: {frame_count // max(1, int(time.time() - self.start_time))}"
                    cv2.putText(display_frame, fps_text, 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    detections_text = f"Objetos: {len(current_detections)}"
                    cv2.putText(display_frame, detections_text, 
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    cv2.imshow('Obstacle Assistant', display_frame)
                    
                    # Salir con 'q'
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("Usuario presionó 'q' para salir")
                        self.running = False
                        break
                
                # Enviar frame a la cola de detección (mantener solo el más reciente)
                if not self.frame_queue.full():
                    try:
                        self.frame_queue.put(frame.copy(), block=False)
                    except queue.Full:
                        # Si está llena, reemplazar con el frame más reciente
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame.copy(), block=False)
                        except queue.Empty:
                            pass
                
                frame_count += 1
                time.sleep(1.0 / VIDEO_FPS)  # Controlar FPS
            
        except Exception as e:
            logger.error(f"Error en hilo de captura de video: {e}")
        finally:
            if self.cap:
                self.cap.release()
            if SHOW_VIDEO_WINDOW:
                cv2.destroyAllWindows()
            logger.info("Hilo de captura de video terminado")
    
    def _detection_thread(self):
        """Hilo para procesamiento de detección de obstáculos."""
        logger.info("Hilo de detección iniciado")
        
        while self.running:
            try:
                # Obtener frame de la cola
                try:
                    frame = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if frame is None:
                    continue
                
                # Realizar detección
                if self.vision_agent:
                    detections = self.vision_agent.detect_objects(frame, force_process=True)
                    
                    # Actualizar detecciones actuales (thread-safe)
                    with self.detections_lock:
                        self.current_detections = detections.copy() if detections else []
                    
                    if detections:
                        # Procesar TODAS las detecciones y generar alertas para cada una
                        print(f"\n📦 Detectados {len(detections)} objeto(s) en este frame")
                        objects_to_announce = []  # Lista de objetos que deben anunciarse
                        
                        for detection in detections:
                            proximity = detection.get('proximity', 'far')
                            obstacle_type = self.vision_agent.get_obstacle_type(detection['name'])
                            is_center = detection.get('is_center', False)
                            
                            # Agregar información adicional para la GUI
                            detection['obstacle_type'] = obstacle_type
                            
                            # Enviar a la GUI
                            if self.detection_queue and not self.detection_queue.full():
                                try:
                                    self.detection_queue.put(detection.copy(), block=False)
                                except:
                                    pass
                            
                            # Determinar prioridad
                            if is_center and proximity == 'close':
                                priority = 'high'
                            elif is_center or proximity == 'close':
                                priority = 'normal'
                            else:
                                priority = 'low'
                            
                            # Generar alerta sonora (solo si está cercano o en el centro)
                            self.obstacle_alert.alert_obstacle(
                                proximity=proximity,
                                obstacle_type=obstacle_type,
                                priority=priority,
                                is_center=is_center
                            )
                            
                            # Anunciar con voz si está cercano O en el centro (zona de peligro)
                            object_name = detection['name']
                            relative_size = detection.get('relative_size', 0)
                            
                            # Determinar si debe anunciarse (cercano O en centro)
                            should_announce = (proximity == 'close') or (is_center and proximity in ['close', 'medium'])
                            
                            if should_announce:
                                # Agregar a la lista de objetos para anunciar
                                objects_to_announce.append({
                                    'name': object_name,
                                    'type': obstacle_type,
                                    'proximity': proximity,
                                    'size': relative_size,
                                    'center': is_center
                                })
                                logger.info(f"🔊 Objeto agregado para anuncio: {object_name} (proximidad: {proximity}, centro: {is_center}, tamaño: {relative_size:.2%})")
                            else:
                                # Solo mostrar en debug si no es para anunciar
                                logger.debug(f"Obstáculo detectado: {detection['name']} - {proximity} - centro: {is_center} (no se anuncia)")
                        
                        # Anunciar TODOS los objetos detectados (uno por uno)
                        if objects_to_announce:
                            print(f"\n🔊 Anunciando {len(objects_to_announce)} objeto(s) cercano(s)...")
                            for obj_info in objects_to_announce:
                                object_name = obj_info['name']
                                obstacle_type = obj_info['type']
                                
                                print(f"\n   📢 Anunciando: {object_name.upper()}")
                                print(f"      - Proximidad: {obj_info['proximity']}")
                                print(f"      - Tamaño: {obj_info['size']:.2%}")
                                print(f"      - En centro: {obj_info['center']}")
                                
                                if self.voice_announcer:
                                    if self.voice_announcer.enabled:
                                        if self.voice_announcer.engine:
                                            try:
                                                self.voice_announcer.announce_close_object(
                                                    object_name,
                                                    obstacle_type
                                                )
                                                print(f"      ✅ Anuncio de '{object_name}' enviado a la cola")
                                            except Exception as e:
                                                print(f"      ❌ Error al anunciar '{object_name}': {e}")
                                                logger.error(f"Error al anunciar objeto {object_name}: {e}")
                                                import traceback
                                                traceback.print_exc()
                                        else:
                                            print(f"      ❌ Motor de voz no está inicializado")
                                    else:
                                        print(f"      ⚠️ Sistema de voz deshabilitado")
                                else:
                                    print(f"      ❌ VoiceAnnouncer no existe")
                                
                                # Pequeña pausa entre anuncios para que no se solapen
                                time.sleep(0.1)
                
                self.frame_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error en hilo de detección: {e}")
                time.sleep(0.1)
        
        logger.info("Hilo de detección terminado")
    
    def _audio_detection_thread(self):
        """Hilo para detección continua de ruido."""
        if not self.audio_detector:
            return
        
        logger.info("Hilo de detección de audio iniciado")
        
        while self.running:
            try:
                # Detectar ruido
                noise_info = self.audio_detector.detect_noise()
                
                if noise_info and noise_info.get('has_noise'):
                    noise_type = noise_info.get('noise_type', 'general')
                    intensity = noise_info.get('intensity', 0.5)
                    
                    # Generar alerta de ruido
                    self.obstacle_alert.alert_noise(noise_type, intensity)
                    
                    logger.debug(f"Ruido detectado: {noise_type} - intensidad: {intensity:.2f}")
                
                # Verificar cada 0.5 segundos
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error en hilo de detección de audio: {e}")
                time.sleep(0.5)
        
        logger.info("Hilo de detección de audio terminado")
    
    def start(self):
        """Inicia el sistema."""
        if self.running:
            logger.warning("El sistema ya está corriendo")
            return
        
        logger.info("Iniciando sistema de detección de obstáculos...")
        self.running = True
        self.start_time = time.time()
        
        # La GUI se ejecutará en el hilo principal, no aquí
        if self.gui:
            logger.info("Interfaz gráfica lista para ejecutarse")
        
        # Iniciar hilos
        self.video_thread = threading.Thread(target=self._video_capture_thread, daemon=True)
        self.video_thread.start()
        
        if OBSTACLE_DETECTION_ENABLED and self.vision_agent:
            self.detection_thread = threading.Thread(target=self._detection_thread, daemon=True)
            self.detection_thread.start()
        
        if ENABLE_AUDIO_DETECTION and self.audio_detector:
            self.audio_thread = threading.Thread(target=self._audio_detection_thread, daemon=True)
            self.audio_thread.start()
        
        logger.info("Sistema iniciado. Presiona 'q' en la ventana de video para salir (si está habilitada)")
        print("\n✅ Sistema iniciado correctamente")
        print("   - Ventana de video: " + ("Activada" if SHOW_VIDEO_WINDOW else "Desactivada"))
        print("   - Interfaz gráfica: " + ("Activada" if self.gui else "Desactivada"))
        print("   - Detección de audio: " + ("Activada" if self.audio_detector else "Desactivada"))
        print("   - Anuncios de voz: " + ("Activada" if (self.voice_announcer and self.voice_announcer.enabled) else "Desactivada"))
        print("\n")
        
        # Esperar a que terminen los hilos
        try:
            if self.video_thread:
                self.video_thread.join()
            if self.detection_thread:
                self.detection_thread.join()
            if self.audio_thread:
                self.audio_thread.join()
        except KeyboardInterrupt:
            logger.info("Interrupción del usuario (Ctrl+C)")
            self.stop()
    
    def stop(self):
        """Detiene el sistema."""
        if not self.running:
            return
        
        logger.info("Deteniendo sistema...")
        self.running = False
        
        # Detener GUI
        if self.gui:
            self.gui.set_status("Deteniendo...", "orange")
            self.gui.stop()
        
        # Detener componentes
        if self.obstacle_alert:
            self.obstacle_alert.stop()
        
        if self.audio_detector:
            self.audio_detector.stop_listening()
        
        if self.voice_announcer:
            self.voice_announcer.stop()
        
        # Esperar a que terminen los hilos
        if self.video_thread:
            self.video_thread.join(timeout=2)
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        if self.gui_thread:
            self.gui_thread.join(timeout=2)
        
        logger.info("Sistema detenido")


def main():
    """Función principal."""
    print("=" * 60)
    print("Asistente Virtual para Detección de Obstáculos")
    print("=" * 60)
    print("\nIniciando sistema...")
    print("Presiona Ctrl+C para detener\n")
    
    assistant = None
    try:
        assistant = ObstacleAssistant()
        
        # Si hay GUI, ejecutarla en el hilo principal
        if assistant.gui:
            # Iniciar sistema de detección en hilos secundarios
            system_thread = threading.Thread(target=assistant.start, daemon=True)
            system_thread.start()
            
            # Esperar un momento para que el sistema inicie
            time.sleep(0.5)
            
            # Actualizar estado de la GUI
            assistant.gui.set_status("Ejecutando", "green")
            
            # Ejecutar GUI en el hilo principal (esto bloquea hasta que se cierre)
            try:
                assistant.gui.run()
            except KeyboardInterrupt:
                print("\n\nInterrupción del usuario. Deteniendo...")
            finally:
                if assistant:
                    assistant.stop()
        else:
            # Sin GUI, ejecutar normalmente
            try:
                assistant.start()
            except KeyboardInterrupt:
                print("\n\nInterrupción del usuario. Deteniendo...")
                if assistant:
                    assistant.stop()
                    
    except KeyboardInterrupt:
        print("\n\nInterrupción del usuario. Deteniendo...")
        if assistant:
            assistant.stop()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nSistema finalizado. ¡Hasta luego!")


if __name__ == "__main__":
    main()

