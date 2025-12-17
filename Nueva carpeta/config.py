"""
Configuración centralizada del sistema de asistencia para invidentes.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de OLLAMA (opcional, para descripciones detalladas)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
ENABLE_OLLAMA = os.getenv('ENABLE_OLLAMA', 'false').lower() == 'true'

# Configuración de YOLO
YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolov8n.pt')
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.5'))
YOLO_PROCESS_EVERY_N_FRAMES = int(os.getenv('YOLO_PROCESS_EVERY_N_FRAMES', '2'))  # Cada 2 frames para tiempo real
YOLO_IMG_SIZE = int(os.getenv('YOLO_IMG_SIZE', '320'))  # Tamaño optimizado para velocidad

# Configuración de captura de video
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '640'))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '480'))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', '30'))
SHOW_VIDEO_WINDOW = os.getenv('SHOW_VIDEO_WINDOW', 'true').lower() == 'true'  # Mostrar ventana de video

# Configuración de detección de obstáculos
OBSTACLE_DETECTION_ENABLED = os.getenv('OBSTACLE_DETECTION_ENABLED', 'true').lower() == 'true'
OBSTACLE_CLOSE_DISTANCE = float(os.getenv('OBSTACLE_CLOSE_DISTANCE', '0.15'))  # 15% del frame = cercano
OBSTACLE_MEDIUM_DISTANCE = float(os.getenv('OBSTACLE_MEDIUM_DISTANCE', '0.08'))  # 8% del frame = medio
OBSTACLE_FAR_DISTANCE = float(os.getenv('OBSTACLE_FAR_DISTANCE', '0.05'))  # 5% del frame = lejano

# Configuración de alertas sonoras
ALERT_ENABLED = os.getenv('ALERT_ENABLED', 'true').lower() == 'true'
ALERT_CLOSE_FREQUENCY = int(os.getenv('ALERT_CLOSE_FREQUENCY', '900'))  # Hz para obstáculo cercano
ALERT_MEDIUM_FREQUENCY = int(os.getenv('ALERT_MEDIUM_FREQUENCY', '600'))  # Hz para obstáculo medio
ALERT_FAR_FREQUENCY = int(os.getenv('ALERT_FAR_FREQUENCY', '300'))  # Hz para obstáculo lejano
ALERT_DURATION = float(os.getenv('ALERT_DURATION', '0.1'))  # Duración del beep en segundos
ALERT_DEBOUNCE_TIME = float(os.getenv('ALERT_DEBOUNCE_TIME', '0.3'))  # Tiempo mínimo entre alertas

# Configuración de detección de audio/ruido
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '44100'))
AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', '1024'))
NOISE_THRESHOLD = float(os.getenv('NOISE_THRESHOLD', '0.2'))
ENABLE_AUDIO_DETECTION = os.getenv('ENABLE_AUDIO_DETECTION', 'true').lower() == 'true'

# Frecuencias características para detección de ruido
SIREN_FREQ_MIN = int(os.getenv('SIREN_FREQ_MIN', '800'))  # Frecuencia mínima de sirenas
SIREN_FREQ_MAX = int(os.getenv('SIREN_FREQ_MAX', '2000'))  # Frecuencia máxima de sirenas
TRAFFIC_FREQ_MIN = int(os.getenv('TRAFFIC_FREQ_MIN', '50'))  # Frecuencia mínima de tráfico
TRAFFIC_FREQ_MAX = int(os.getenv('TRAFFIC_FREQ_MAX', '500'))  # Frecuencia máxima de tráfico

# Configuración de TTS (opcional)
TTS_ENGINE = os.getenv('TTS_ENGINE', 'pyttsx3')  # 'gtts' o 'pyttsx3'
TTS_LANGUAGE = os.getenv('TTS_LANGUAGE', 'es')
TTS_RATE = int(os.getenv('TTS_RATE', '150'))
TTS_VOLUME = float(os.getenv('TTS_VOLUME', '0.8'))
ENABLE_VOICE_DESCRIPTIONS = os.getenv('ENABLE_VOICE_DESCRIPTIONS', 'true').lower() == 'true'  # Activado por defecto para objetos cercanos

# Modos de operación
OPERATION_MODE = os.getenv('OPERATION_MODE', 'silent')  # 'silent' (solo alertas) o 'full' (alertas + voz)
SENSITIVITY = os.getenv('SENSITIVITY', 'medium')  # 'high', 'medium', 'low'
ENABLE_GUI = os.getenv('ENABLE_GUI', 'true').lower() == 'true'  # Habilitar interfaz gráfica

# Configuración de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'obstacle_assistant.log')

