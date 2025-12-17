"""
Configuración centralizada del sistema de asistencia visual.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de OLLAMA
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

# Configuración de PostgreSQL / Supabase
# 
# OPCIÓN 1: Cliente Supabase (Project URL + API Key) - RECOMENDADO
SUPABASE_URL = os.getenv('SUPABASE_URL')  # https://[PROJECT_REF].supabase.co
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # API Key (anon key o service_role key)

# OPCIÓN 2: URL completa de conexión PostgreSQL directa
DATABASE_URL = os.getenv('DATABASE_URL')

# OPCIÓN 3: Componentes de Supabase para construir URL PostgreSQL
SUPABASE_PROJECT_REF = os.getenv('SUPABASE_PROJECT_REF')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')
SUPABASE_REGION = os.getenv('SUPABASE_REGION', 'us-east-1')
SUPABASE_CONNECTION_MODE = os.getenv('SUPABASE_CONNECTION_MODE', 'pooler')  # 'pooler' o 'direct'

# Construir DATABASE_URL si no está definida pero sí los componentes de Supabase
if not DATABASE_URL and SUPABASE_PROJECT_REF and SUPABASE_DB_PASSWORD:
    if SUPABASE_CONNECTION_MODE == 'direct':
        # Conexión directa (sin pooler)
        DATABASE_URL = f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
    else:
        # Connection Pooling (recomendado para aplicaciones)
        DATABASE_URL = f"postgresql://postgres.{SUPABASE_PROJECT_REF}:{SUPABASE_DB_PASSWORD}@aws-0-{SUPABASE_REGION}.pooler.supabase.com:6543/postgres"

# Fallback a PostgreSQL local si nada está configurado
if not DATABASE_URL and not (SUPABASE_URL and SUPABASE_KEY):
    DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/vision_assistant'

# Determinar método de conexión
USE_SUPABASE_CLIENT = bool(SUPABASE_URL and SUPABASE_KEY)

# Configuración de YOLO
YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolov8n.pt')
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.5'))
YOLO_PROCESS_EVERY_N_FRAMES = int(os.getenv('YOLO_PROCESS_EVERY_N_FRAMES', '5'))

# Configuración de TTS
TTS_ENGINE = os.getenv('TTS_ENGINE', 'gtts')  # 'gtts' o 'pyttsx3'
TTS_LANGUAGE = os.getenv('TTS_LANGUAGE', 'es')
TTS_RATE = int(os.getenv('TTS_RATE', '150'))  # Velocidad de habla
TTS_VOLUME = float(os.getenv('TTS_VOLUME', '0.8'))  # Volumen (0.0 a 1.0)

# Configuración de captura de video
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '640'))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '480'))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', '30'))

# Configuración de procesamiento
MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '500'))  # Aumentado para descripciones completas
AUDIO_QUEUE_MAX_SIZE = int(os.getenv('AUDIO_QUEUE_MAX_SIZE', '3'))
CACHE_DESCRIPTIONS = os.getenv('CACHE_DESCRIPTIONS', 'true').lower() == 'true'

# Configuración de detección de audio/ruido
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '44100'))
AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', '1024'))
NOISE_THRESHOLD = float(os.getenv('NOISE_THRESHOLD', '0.2'))  # Umbral para considerar ruido significativo
ENABLE_AUDIO_DETECTION = os.getenv('ENABLE_AUDIO_DETECTION', 'true').lower() == 'true'

# Configuración de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'vision_assistant.log')

