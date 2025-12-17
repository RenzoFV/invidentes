"""
Funciones auxiliares para validación, formateo y logging.
"""

import logging
import cv2
import requests
from typing import Tuple, List, Dict
from config import OLLAMA_BASE_URL, CAMERA_INDEX, LOG_LEVEL, LOG_FILE


def setup_logging():
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def validate_camera_access(camera_index: int = None) -> Tuple[bool, str]:
    """
    Valida si la cámara está disponible y accesible.
    
    Args:
        camera_index: Índice de la cámara a validar
        
    Returns:
        Tuple (éxito, mensaje)
    """
    if camera_index is None:
        camera_index = CAMERA_INDEX
    
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return False, f"No se pudo abrir la cámara {camera_index}"
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False, f"La cámara {camera_index} no puede capturar frames"
        
        return True, f"Cámara {camera_index} disponible"
    
    except Exception as e:
        return False, f"Error al acceder a la cámara: {str(e)}"


def validate_ollama_connection(base_url: str = None) -> Tuple[bool, str]:
    """
    Valida si OLLAMA está disponible y corriendo.
    
    Args:
        base_url: URL base de OLLAMA
        
    Returns:
        Tuple (éxito, mensaje)
    """
    if base_url is None:
        base_url = OLLAMA_BASE_URL
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "OLLAMA está disponible"
        else:
            return False, f"OLLAMA respondió con código {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar a OLLAMA. ¿Está corriendo?"
    except requests.exceptions.Timeout:
        return False, "Timeout al conectar con OLLAMA"
    except Exception as e:
        return False, f"Error al validar OLLAMA: {str(e)}"


def format_spatial_description(
    detections: List[Dict],
    frame_width: int = 640,
    frame_height: int = 480
) -> str:
    """
    Formatea las detecciones con información espacial para contexto de invidentes.
    
    Args:
        detections: Lista de detecciones con formato YOLO
        frame_width: Ancho del frame
        frame_height: Alto del frame
        
    Returns:
        Descripción formateada con posiciones relativas
    """
    if not detections:
        return "No se detectaron objetos en el entorno."
    
    descriptions = []
    
    for det in detections:
        obj_name = det.get('name', 'objeto')
        confidence = det.get('confidence', 0)
        bbox = det.get('bbox', {})
        
        # Calcular posición relativa
        center_x = bbox.get('x_center', frame_width / 2)
        center_y = bbox.get('y_center', frame_height / 2)
        
        # Determinar posición horizontal
        if center_x < frame_width * 0.33:
            horizontal_pos = "a tu izquierda"
        elif center_x > frame_width * 0.67:
            horizontal_pos = "a tu derecha"
        else:
            horizontal_pos = "frente a ti"
        
        # Determinar posición vertical
        if center_y < frame_height * 0.33:
            vertical_pos = "arriba"
        elif center_y > frame_height * 0.67:
            vertical_pos = "abajo"
        else:
            vertical_pos = "a la altura"
        
        # Construir descripción
        conf_text = f" (confianza: {confidence:.0%})" if confidence < 0.7 else ""
        desc = f"{obj_name} {horizontal_pos}, {vertical_pos}{conf_text}"
        descriptions.append(desc)
    
    return ". ".join(descriptions) + "."


def calculate_bbox_position(
    x1: float, y1: float, x2: float, y2: float,
    frame_width: int, frame_height: int
) -> Dict[str, float]:
    """
    Calcula la posición del centro de un bounding box.
    
    Args:
        x1, y1: Coordenadas superior izquierda
        x2, y2: Coordenadas inferior derecha
        frame_width: Ancho del frame
        frame_height: Alto del frame
        
    Returns:
        Diccionario con x_center, y_center normalizados
    """
    return {
        'x_center': (x1 + x2) / 2,
        'y_center': (y1 + y2) / 2,
        'width': x2 - x1,
        'height': y2 - y1
    }

