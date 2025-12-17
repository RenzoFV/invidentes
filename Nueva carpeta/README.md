# Asistente Virtual para Detección de Obstáculos

Sistema de asistencia en tiempo real para personas invidentes que detecta obstáculos usando visión por computadora y alertas sonoras.

## Características

- ✅ **Detección de obstáculos en tiempo real** usando YOLO v8
- ✅ **Interfaz gráfica sencilla** que muestra objetos detectados en tiempo real
- ✅ **Alertas sonoras** según proximidad y tipo de obstáculo
- ✅ **Detección de ruido avanzada** (sirenas, tráfico, voces)
- ✅ **Cálculo de proximidad** basado en tamaño relativo de objetos
- ✅ **Procesamiento optimizado** para tiempo real (30+ FPS)
- ✅ **Modo headless** (sin ventana de video) o con visualización

## Requisitos

- Python 3.8 o superior
- Cámara web
- Micrófono (opcional, para detección de ruido)

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Descargar modelo YOLO (se descarga automáticamente la primera vez):
   - El modelo `yolov8n.pt` se descargará automáticamente

## Configuración

Crear archivo `.env` (opcional) con las siguientes variables:

```env
# Cámara
CAMERA_INDEX=0
VIDEO_WIDTH=640
VIDEO_HEIGHT=480
VIDEO_FPS=30
SHOW_VIDEO_WINDOW=true

# YOLO
YOLO_MODEL=yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_PROCESS_EVERY_N_FRAMES=2
YOLO_IMG_SIZE=320

# Alertas
ALERT_ENABLED=true
ALERT_CLOSE_FREQUENCY=900
ALERT_MEDIUM_FREQUENCY=600
ALERT_FAR_FREQUENCY=300

# Audio
ENABLE_AUDIO_DETECTION=true
NOISE_THRESHOLD=0.2

# Interfaz
ENABLE_GUI=true  # Habilitar interfaz gráfica

# Modo
OPERATION_MODE=silent  # 'silent' o 'full'
SENSITIVITY=medium  # 'high', 'medium', 'low'
```

## Uso

Ejecutar la aplicación:

```bash
python obstacle_assistant.py
```

### Interfaz Gráfica

La interfaz muestra en tiempo real:
- **Objetos detectados** con su nombre (person, car, chair, etc.)
- **Confianza** de la detección (porcentaje)
- **Proximidad** (cercano/medio/lejano) con indicadores visuales
- **Tipo de obstáculo** (persona, vehículo, mueble, objeto)
- **Zona de peligro** (si está en el centro del frame)
- **Estadísticas** de detecciones totales

### Controles

- **'q'** en la ventana de video: Salir (si `SHOW_VIDEO_WINDOW=true`)
- **Ctrl+C**: Salir desde terminal
- **Botón "Limpiar"** en la interfaz: Limpia el historial de detecciones

## Sistema de Alertas

### Alertas por Proximidad

- **Obstáculo cercano** (< 1m estimado): Beep agudo continuo (900 Hz)
- **Obstáculo medio** (1-3m): Beep medio intermitente (600 Hz)
- **Obstáculo lejano** (> 3m): Beep grave ocasional (300 Hz)

### Alertas por Tipo

- **Personas**: Tono ligeramente más agudo
- **Vehículos**: Tono ligeramente más grave
- **Objetos estáticos**: Tono estándar

### Alertas de Ruido

- **Sirenas**: Tono de alerta urgente (1200 Hz)
- **Tráfico**: Tono grave (400 Hz)
- **Voces**: Tono medio (500 Hz)

## Estructura del Proyecto

```
Nueva carpeta/
├── obstacle_assistant.py    # Aplicación principal
├── config.py                # Configuración centralizada
├── requirements.txt         # Dependencias
├── README.md                # Este archivo
├── agents/
│   └── vision_agent.py      # Detección de objetos con YOLO
├── modules/
│   ├── obstacle_alert.py    # Sistema de alertas sonoras
│   └── audio_detector.py    # Detección avanzada de ruido
├── gui/
│   └── obstacle_gui.py       # Interfaz gráfica
└── utils/
    └── helpers.py           # Funciones auxiliares
```

## Modos de Operación

### Modo Silencioso (por defecto)
- Solo alertas sonoras
- Sin descripciones de voz
- Ideal para uso continuo

### Modo Completo
- Alertas sonoras + descripciones de voz
- Requiere TTS configurado
- Más informativo pero más verboso

## Optimizaciones

- Procesamiento de frames optimizado (320x320 para YOLO)
- Detección cada 2 frames (configurable)
- Threading para procesamiento paralelo
- Buffer mínimo para menor latencia
- Sistema de debounce para evitar alertas excesivas

## Solución de Problemas

### La cámara no se abre
- Verificar que la cámara no esté siendo usada por otra aplicación
- Cambiar `CAMERA_INDEX` en la configuración
- Verificar permisos de la cámara

### No hay sonido
- Verificar que pygame esté instalado: `pip install pygame`
- En Windows, verificar que winsound funcione
- Verificar volumen del sistema

### Detección lenta
- Reducir `YOLO_IMG_SIZE` a 320 o menos
- Aumentar `YOLO_PROCESS_EVERY_N_FRAMES` a 3 o 4
- Deshabilitar ventana de video: `SHOW_VIDEO_WINDOW=false`

## Licencia

Este proyecto es de código abierto.

