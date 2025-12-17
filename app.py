"""
Aplicación principal Streamlit para el sistema de asistencia visual.
"""

import streamlit as st
import cv2
import numpy as np
import logging
import time
from typing import Optional

# Configuración de logging
from utils.helpers import setup_logging, validate_camera_access, validate_ollama_connection
from agents.vision_agent import VisionAgent
from agents.language_agent import LanguageAgent
from modules.audio_module import AudioManager
from modules.database_manager import DatabaseManager
from modules.audio_detector import AudioDetector
from config import ENABLE_AUDIO_DETECTION
from config import (
    CAMERA_INDEX, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    TTS_VOLUME, TTS_RATE
)

# Configurar logging
logger = setup_logging()

# Configuración de página Streamlit
st.set_page_config(
    page_title="Asistente Visual para Invidentes",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para accesibilidad
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 24px;
        background-color: #FFD700;
        color: #000000;
        border: 3px solid #000000;
        border-radius: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FFA500;
        border-color: #000000;
    }
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #000000;
        background-color: #FFD700;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    .status-box {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .status-ok {
        background-color: #90EE90;
        color: #000000;
        border: 2px solid #000000;
    }
    .status-error {
        background-color: #FF6B6B;
        color: #FFFFFF;
        border: 2px solid #000000;
    }
    .status-warning {
        background-color: #FFD700;
        color: #000000;
        border: 2px solid #000000;
    }
</style>
""", unsafe_allow_html=True)


def initialize_components():
    """Inicializa todos los componentes del sistema."""
    if 'initialized' not in st.session_state:
        try:
            # Inicializar base de datos
            st.session_state.db_manager = DatabaseManager()
            logger.info("DatabaseManager inicializado")
            
            # Crear/obtener usuario por defecto
            user = st.session_state.db_manager.create_or_get_user("default")
            st.session_state.user_id = user.get('id', 1)
            st.session_state.user_preferences = {
                'velocidad_habla': user.get('velocidad_habla', TTS_RATE),
                'volumen': user.get('volumen', TTS_VOLUME),
                'modo_detallado': user.get('modo_detallado', False)
            }
            
            # Inicializar audio
            st.session_state.audio_manager = AudioManager()
            st.session_state.audio_manager.set_volume(st.session_state.user_preferences['volumen'])
            st.session_state.audio_manager.set_rate(st.session_state.user_preferences['velocidad_habla'])
            logger.info("AudioManager inicializado")
            
            # Inicializar agente de visión
            st.session_state.vision_agent = VisionAgent()
            logger.info("VisionAgent inicializado")
            
            # Inicializar agente de lenguaje
            st.session_state.language_agent = LanguageAgent(
                db_manager=st.session_state.db_manager
            )
            logger.info("LanguageAgent inicializado")
            
            # Estado de detección
            st.session_state.detection_active = False
            st.session_state.last_detection_time = 0
            st.session_state.last_description = ""
            st.session_state.cap = None
            # NO inicializar frame_placeholder aquí, se crea en main()
            
            # Inicializar detector de audio si está habilitado
            if ENABLE_AUDIO_DETECTION:
                try:
                    st.session_state.audio_detector = AudioDetector()
                    st.session_state.audio_detector.start_listening()
                    logger.info("Detector de audio inicializado")
                except Exception as e:
                    logger.warning(f"No se pudo inicializar detector de audio: {e}")
                    st.session_state.audio_detector = None
            else:
                st.session_state.audio_detector = None
            
            st.session_state.initialized = True
            logger.info("Sistema inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes: {e}")
            st.error(f"Error al inicializar el sistema: {e}")
            st.session_state.initialized = False


def check_system_status():
    """Verifica el estado de los componentes del sistema."""
    status = {
        'camera': False,
        'ollama': False,
        'message': ''
    }
    
    # Verificar cámara
    camera_ok, camera_msg = validate_camera_access()
    status['camera'] = camera_ok
    
    # Verificar OLLAMA
    ollama_ok, ollama_msg = validate_ollama_connection()
    status['ollama'] = ollama_ok
    
    if camera_ok and ollama_ok:
        status['message'] = "✅ Sistema listo"
    elif not camera_ok:
        status['message'] = f"⚠️ {camera_msg}"
    elif not ollama_ok:
        status['message'] = f"⚠️ {ollama_msg}. Se usará modo simple (descripciones básicas)."
    else:
        status['message'] = "⚠️ Problemas detectados"
    
    return status


def start_detection():
    """Inicia la detección de objetos."""
    try:
        # Cerrar cámara anterior si existe
        if st.session_state.cap:
            try:
                st.session_state.cap.release()
            except:
                pass
        
        # Crear nueva captura con backend específico para Windows (DirectShow)
        # Esto ayuda a evitar errores MSMF
        st.session_state.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        
        if not st.session_state.cap.isOpened():
            # Fallback a backend por defecto
            logger.warning("DirectShow falló, intentando backend por defecto")
            st.session_state.cap = cv2.VideoCapture(CAMERA_INDEX)
        
        if not st.session_state.cap.isOpened():
            raise Exception("No se pudo abrir la cámara")
        
        # Configurar propiedades de la cámara (después de abrir)
        try:
            st.session_state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
            st.session_state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
            st.session_state.cap.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
            # Reducir buffer para menor latencia
            st.session_state.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as prop_error:
            logger.warning(f"Error al configurar propiedades de cámara: {prop_error}")
        
        # Dar tiempo para que la cámara se inicialice
        time.sleep(0.5)
        
        # Intentar leer un frame para verificar que la cámara funciona
        ret, frame = st.session_state.cap.read()
        if not ret or frame is None:
            # Intentar una vez más
            time.sleep(0.3)
            ret, frame = st.session_state.cap.read()
            if not ret or frame is None:
                st.session_state.cap.release()
                raise Exception("La cámara no puede capturar frames. Verifica que no esté siendo usada por otra aplicación.")
        
        st.session_state.detection_active = True
        st.session_state.vision_agent.reset_frame_count()
        st.session_state.last_detection_time = 0
        logger.info("Detección iniciada correctamente")
        
        # Mensaje de audio
        try:
            st.session_state.audio_manager.speak(
                "Detección iniciada. Analizando el entorno.",
                priority=True
            )
        except Exception as audio_error:
            logger.warning(f"Error al reproducir audio inicial: {audio_error}")
        
    except Exception as e:
        logger.error(f"Error al iniciar detección: {e}")
        st.error(f"Error: {e}")
        if 'cap' in st.session_state and st.session_state.cap:
            try:
                st.session_state.cap.release()
            except:
                pass
            st.session_state.cap = None
        st.session_state.detection_active = False
        try:
            st.session_state.audio_manager.speak(
                f"Error al iniciar la cámara: {str(e)}",
                priority=True
            )
        except:
            pass


def stop_detection():
    """Detiene la detección de objetos."""
    st.session_state.detection_active = False
    
    if st.session_state.cap:
        st.session_state.cap.release()
        st.session_state.cap = None
    
    # Detener detector de audio si existe
    if 'audio_detector' in st.session_state and st.session_state.audio_detector:
        try:
            st.session_state.audio_detector.stop_listening()
        except:
            pass
    
    st.session_state.audio_manager.stop()
    st.session_state.audio_manager.speak("Detección detenida.", priority=True)
    logger.info("Detección detenida")


def process_video_and_detection():
    """Procesa video continuo y detección periódica en un solo ciclo."""
    if not st.session_state.cap or not st.session_state.cap.isOpened():
        # Intentar reabrir cámara
        try:
            st.session_state.cap.open(CAMERA_INDEX, cv2.CAP_DSHOW)
        except:
            pass
        return
    
    try:
        # Leer UN frame para video y detección
        ret, frame = st.session_state.cap.read()
        
        if not ret or frame is None:
            return
        
        # SIEMPRE actualizar el video (video continuo)
        if 'frame_placeholder' in st.session_state and st.session_state.frame_placeholder is not None:
            try:
                if frame.size > 0:
                    # Convertir BGR a RGB para Streamlit
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Actualizar la imagen - video continuo
                    st.session_state.frame_placeholder.image(
                        frame_rgb, 
                        channels="RGB", 
                        width='stretch'
                    )
            except Exception as img_error:
                logger.warning(f"Error al mostrar imagen: {img_error}")
        
        # Detección solo cada 3 segundos (no en cada frame)
        current_time = time.time()
        time_since_last = current_time - st.session_state.last_detection_time
        
        if time_since_last >= 3.0:
            # Es momento de hacer detección
            try:
                detections = st.session_state.vision_agent.detect_objects(frame)
            except Exception as det_error:
                logger.error(f"Error en detección de objetos: {det_error}")
                detections = []
            
            # Detectar ruido/audio si está habilitado
            noise_info = None
            if ENABLE_AUDIO_DETECTION and 'audio_detector' in st.session_state and st.session_state.audio_detector:
                try:
                    noise_info = st.session_state.audio_detector.detect_noise()
                except Exception as audio_error:
                    logger.warning(f"Error al detectar ruido: {audio_error}")
            
            # Combinar detecciones visuales con información de audio
            if detections or noise_info:
                try:
                    detailed = st.session_state.user_preferences.get('modo_detallado', False)
                    
                    # Agregar información de ruido a las detecciones si existe
                    detections_with_audio = detections.copy() if detections else []
                    if noise_info:
                        detections_with_audio.append({
                            'name': 'ruido',
                            'confidence': noise_info.get('intensity', 0.5),
                            'audio_info': noise_info
                        })
                    
                    description = st.session_state.language_agent.generate_description(
                        detections_with_audio,
                        detailed=detailed
                    )
                    
                    # Solo hablar si la descripción es diferente
                    # Y esperar a que termine el audio actual antes de reproducir uno nuevo
                    if description != st.session_state.last_description:
                        # Esperar a que termine el audio actual si está reproduciendo
                        if st.session_state.audio_manager.is_busy():
                            # Esperar un poco más antes de interrumpir
                            time.sleep(0.5)
                        
                        st.session_state.audio_manager.speak(description)
                        st.session_state.last_description = description
                        st.session_state.last_detection_time = current_time
                        
                        # Actualizar descripción en UI
                        if 'description_placeholder' in st.session_state:
                            st.session_state.description_placeholder.info(description)
                        
                        # Guardar en base de datos
                        try:
                            st.session_state.db_manager.save_detection(
                                st.session_state.user_id,
                                detections,
                                description
                            )
                        except Exception as e:
                            logger.error(f"Error al guardar detección: {e}")
                except Exception as desc_error:
                    logger.error(f"Error al generar descripción: {desc_error}")
            else:
                # Actualizar tiempo aunque no haya detecciones
                st.session_state.last_detection_time = current_time
    
    except cv2.error as cv_error:
        logger.error(f"Error de OpenCV: {cv_error}")
        # Intentar reinicializar la cámara
        try:
            if st.session_state.cap:
                st.session_state.cap.release()
            time.sleep(0.3)
            st.session_state.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        except:
            pass
    except Exception as e:
        logger.error(f"Error al procesar video: {e}")


def main():
    """Función principal de la aplicación."""
    # Título principal
    st.markdown('<div class="main-header">👁️ Asistente Visual para Invidentes</div>', unsafe_allow_html=True)
    
    # Inicializar componentes
    initialize_components()
    
    if not st.session_state.get('initialized', False):
        st.error("No se pudo inicializar el sistema. Por favor, revisa los logs.")
        return
    
    # Sidebar con controles
    with st.sidebar:
        st.header("⚙️ Controles")
        
        # Estado del sistema
        status = check_system_status()
        status_class = "status-ok" if status['camera'] and status['ollama'] else "status-warning"
        st.markdown(
            f'<div class="status-box {status_class}">{status["message"]}</div>',
            unsafe_allow_html=True
        )
        
        st.divider()
        
        # Botón principal de inicio/detención
        if st.session_state.detection_active:
            if st.button("🛑 DETENER DETECCIÓN", key="stop_btn"):
                stop_detection()
                st.rerun()
        else:
            if st.button("▶️ INICIAR DETECCIÓN", key="start_btn"):
                start_detection()
                st.rerun()
        
        st.divider()
        
        # Controles de audio
        st.subheader("🔊 Configuración de Audio")
        
        # Asegurar que el valor sea float
        volumen_actual = st.session_state.user_preferences.get('volumen', TTS_VOLUME)
        if isinstance(volumen_actual, int):
            volumen_actual = float(volumen_actual)
        
        volume = st.slider(
            "Volumen",
            min_value=0.0,
            max_value=1.0,
            value=volumen_actual,
            step=0.1,
            key="volume_slider"
        )
        
        volumen_guardado = st.session_state.user_preferences.get('volumen', TTS_VOLUME)
        if isinstance(volumen_guardado, int):
            volumen_guardado = float(volumen_guardado)
        
        if volume != volumen_guardado:
            st.session_state.audio_manager.set_volume(volume)
            st.session_state.user_preferences['volumen'] = float(volume)
            st.session_state.db_manager.update_user_preferences(
                st.session_state.user_id,
                {'volumen': volume}
            )
        
        rate = st.slider(
            "Velocidad de Habla",
            min_value=50,
            max_value=300,
            value=st.session_state.user_preferences.get('velocidad_habla', TTS_RATE),
            step=10,
            key="rate_slider"
        )
        
        if rate != st.session_state.user_preferences.get('velocidad_habla'):
            st.session_state.audio_manager.set_rate(rate)
            st.session_state.user_preferences['velocidad_habla'] = rate
            st.session_state.db_manager.update_user_preferences(
                st.session_state.user_id,
                {'velocidad_habla': rate}
            )
        
        st.divider()
        
        # Modo detallado
        modo_detallado = st.checkbox(
            "Modo Descripción Detallada",
            value=st.session_state.user_preferences.get('modo_detallado', False),
            key="detailed_mode"
        )
        
        if modo_detallado != st.session_state.user_preferences.get('modo_detallado'):
            st.session_state.user_preferences['modo_detallado'] = modo_detallado
            st.session_state.db_manager.update_user_preferences(
                st.session_state.user_id,
                {'modo_detallado': modo_detallado}
            )
        
        st.divider()
        
        # Información del sistema
        st.subheader("ℹ️ Información")
        st.info("""
        **Instrucciones:**
        1. Haz clic en "INICIAR DETECCIÓN"
        2. El sistema analizará tu entorno
        3. Escucharás descripciones de los objetos detectados
        4. Usa los controles para ajustar volumen y velocidad
        """)
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Vista de Cámara")
        st.session_state.frame_placeholder = st.empty()
        
        if not st.session_state.detection_active:
            st.info("Presiona 'INICIAR DETECCIÓN' para comenzar")
        else:
            st.success("✅ Detección activa")
    
    with col2:
        st.subheader("📝 Última Descripción")
        description_placeholder = st.empty()
        st.session_state.description_placeholder = description_placeholder
        
        if st.session_state.last_description:
            description_placeholder.info(st.session_state.last_description)
        else:
            description_placeholder.info("Esperando detecciones...")
    
    # Loop de procesamiento - video continuo con detección periódica
    if st.session_state.detection_active:
        # Procesar video (siempre se actualiza) y detección (solo cada 3 segundos)
        # El video se actualiza en cada iteración para mantener fluidez
        # La detección solo ocurre cada 3 segundos para no saturar el sistema
        process_video_and_detection()
        
        # Rerun frecuente para mantener video fluido (~12-15 FPS visual)
        # El video se actualiza cada rerun, pero la detección solo cada 3 segundos
        time.sleep(0.08)  # ~12 FPS para video fluido sin saturar
        st.rerun()


if __name__ == "__main__":
    main()

