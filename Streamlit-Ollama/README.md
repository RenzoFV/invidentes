# 👁️ Sistema de Asistencia Visual para Invidentes

Sistema de asistencia en tiempo real que utiliza visión por computadora e inteligencia artificial para describir el entorno a personas con discapacidad visual a través de audio en español.

## 📋 Descripción

Este sistema combina:
- **YOLO** para detección de objetos en tiempo real
- **OLLAMA** (Llama 3) para generar descripciones naturales en español
- **PostgreSQL** para almacenar perfiles de usuario y cachear descripciones
- **Streamlit** como interfaz web accesible
- **Síntesis de voz** (gTTS/pyttsx3) para convertir texto a audio

## 🏗️ Arquitectura

El sistema está basado en una arquitectura de agentes especializados:

- **Agente de Visión** (`VisionAgent`): Utiliza YOLO para detectar objetos en los frames de la cámara
- **Agente de Lenguaje** (`LanguageAgent`): Interactúa con OLLAMA para generar descripciones contextuales y naturales
- **Módulo de Audio** (`AudioManager`): Convierte las descripciones en voz usando gTTS o pyttsx3
- **Gestor de Base de Datos** (`DatabaseManager`): Gestiona perfiles de usuario, historial y cache

## 🚀 Requisitos Previos

### Software Necesario

1. **Python 3.9+**
   ```bash
   python --version
   ```

2. **Supabase (Base de Datos PostgreSQL en la nube)**
   - Crear una cuenta gratuita en [supabase.com](https://supabase.com)
   - Crear un nuevo proyecto
   - Obtener la URL de conexión desde: **Settings > Database > Connection string**
   - El sistema creará automáticamente las tablas necesarias al iniciar
   - **📖 Ver guía detallada:** [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
   
   **Alternativa: PostgreSQL Local**
   - Si prefieres usar PostgreSQL local, instalar desde [postgresql.org](https://www.postgresql.org/download/)
   - Crear la base de datos:
   ```sql
   CREATE DATABASE vision_assistant;
   ```

3. **OLLAMA**
   - Instalar desde [ollama.ai](https://ollama.ai/)
   - Descargar modelo Llama 3:
   ```bash
   ollama pull llama3
   # O para mejor soporte en español:
   ollama pull llama3.2
   ```

4. **Cámara Web**
   - Asegúrate de que tu cámara esté conectada y accesible

## 📦 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd LAB-14
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones:

**Para Supabase:**
- `DATABASE_URL`: Copia la Connection string de Supabase (Settings > Database)
  - Formato: `postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
  - El sistema detectará automáticamente Supabase y configurará SSL

**Para PostgreSQL Local:**
- `DATABASE_URL`: `postgresql://usuario:contraseña@localhost:5432/vision_assistant`

**Otras configuraciones:**
- `OLLAMA_BASE_URL`: URL de tu servidor OLLAMA (por defecto: http://localhost:11434)
- `OLLAMA_MODEL`: Modelo a usar (por defecto: llama3)

## 🎯 Uso

### 1. Iniciar OLLAMA (si no está corriendo como servicio)

```bash
ollama serve
```

### 2. Iniciar la aplicación Streamlit

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### 3. Usar la aplicación

1. **Verificar estado**: El sistema verificará automáticamente la cámara y OLLAMA
2. **Iniciar detección**: Haz clic en el botón grande "▶️ INICIAR DETECCIÓN"
3. **Ajustar controles**: Usa los sliders en la barra lateral para ajustar volumen y velocidad
4. **Modo detallado**: Activa el checkbox para descripciones más completas
5. **Detener**: Haz clic en "🛑 DETENER DETECCIÓN" cuando termines

## ⚙️ Configuración Avanzada

### Variables de Entorno Principales

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `OLLAMA_BASE_URL` | URL del servidor OLLAMA | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo de OLLAMA a usar | `llama3` |
| `DATABASE_URL` | Conexión a PostgreSQL | `postgresql://postgres:postgres@localhost:5432/vision_assistant` |
| `YOLO_MODEL` | Modelo YOLO | `yolov8n.pt` |
| `YOLO_CONFIDENCE_THRESHOLD` | Umbral de confianza | `0.5` |
| `TTS_ENGINE` | Motor TTS (`gtts` o `pyttsx3`) | `gtts` |
| `CAMERA_INDEX` | Índice de la cámara | `0` |

### Optimización de Rendimiento

- **YOLO_PROCESS_EVERY_N_FRAMES**: Procesa cada N frames (por defecto: 5)
  - Aumentar este valor reduce la carga de CPU pero disminuye la frecuencia de detecciones
- **AUDIO_QUEUE_MAX_SIZE**: Tamaño máximo de la cola de audio (por defecto: 3)
  - Evita acumulación excesiva de mensajes de audio

## 🐛 Solución de Problemas

### Error: "No se pudo abrir la cámara"
- Verifica que la cámara esté conectada
- Asegúrate de que no esté siendo usada por otra aplicación
- Prueba cambiar `CAMERA_INDEX` en `.env` (0, 1, 2, etc.)

### Error: "No se pudo conectar a OLLAMA"
- Verifica que OLLAMA esté corriendo: `ollama list`
- Comprueba que el modelo esté descargado: `ollama pull llama3`
- Verifica la URL en `.env`

### Error: "Error al conectar con PostgreSQL/Supabase"
- **Para Supabase:**
  - Verifica que la URL de conexión sea correcta
  - Asegúrate de copiar la Connection string completa desde Supabase
  - Verifica que el proyecto de Supabase esté activo
- **Para PostgreSQL Local:**
  - Verifica que PostgreSQL esté corriendo
  - Comprueba las credenciales en `DATABASE_URL`
  - Asegúrate de que la base de datos exista

### Audio no funciona
- Si usas `gtts`, requiere conexión a internet
- Si usas `pyttsx3`, verifica que las voces estén instaladas en tu sistema
- En Windows, puede requerir permisos adicionales

## 📁 Estructura del Proyecto

```
LAB-14/
├── app.py                 # Aplicación principal Streamlit
├── config.py             # Configuración centralizada
├── requirements.txt      # Dependencias
├── .env.example         # Plantilla de variables de entorno
├── README.md            # Este archivo
├── agents/
│   ├── __init__.py
│   ├── vision_agent.py  # Agente de detección YOLO
│   └── language_agent.py # Agente de procesamiento OLLAMA
├── modules/
│   ├── __init__.py
│   ├── audio_module.py  # Síntesis de voz
│   └── database_manager.py # Gestión PostgreSQL
└── utils/
    ├── __init__.py
    └── helpers.py       # Utilidades y validaciones
```

## 🔒 Consideraciones de Seguridad y Privacidad

- Las imágenes de la cámara se procesan localmente y no se almacenan
- Solo se guardan en la base de datos las descripciones generadas (texto)
- El sistema funciona completamente offline (excepto gTTS que requiere internet)
- Los datos del usuario se almacenan localmente en PostgreSQL

## 🚧 Limitaciones y Mejoras Futuras

### Limitaciones Actuales
- Streamlit no es ideal para uso móvil nativo (considerar Flutter/Kotlin para producción)
- Dependencia de buena iluminación para detecciones precisas
- Latencia variable según el hardware disponible

### Mejoras Propuestas
- [ ] Aplicación móvil nativa (Flutter/Kotlin)
- [ ] Detección de obstáculos en tiempo real más precisa
- [ ] Reconocimiento de texto (OCR) para leer señales y etiquetas
- [ ] Navegación asistida con GPS
- [ ] Modo offline completo con modelos locales optimizados
- [ ] Soporte para múltiples idiomas

## 📝 Licencia

Este proyecto es un prototipo educativo desarrollado para asistencia a personas con discapacidad visual.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para mejoras.

## 📞 Soporte

Para problemas o preguntas:
1. Revisa la sección de Solución de Problemas
2. Verifica los logs en `vision_assistant.log`
3. Asegúrate de que todos los requisitos previos estén instalados y configurados

---

**Nota**: Este es un prototipo de investigación. Para uso en producción, se recomienda desarrollar una aplicación móvil nativa con optimizaciones adicionales.

