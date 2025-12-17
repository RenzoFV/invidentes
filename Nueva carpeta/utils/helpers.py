"""
Funciones auxiliares para validación y cálculos.
"""

import logging
import cv2
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


def calculate_bbox_position(
    x1: float, y1: float, x2: float, y2: float,
    frame_width: int, frame_height: int
) -> Dict[str, float]:
    """
    Calcula la posición del centro de un bounding box y su tamaño relativo.
    
    Args:
        x1, y1: Coordenadas superior izquierda
        x2, y2: Coordenadas inferior derecha
        frame_width: Ancho del frame
        frame_height: Alto del frame
        
    Returns:
        Diccionario con x_center, y_center, width, height y tamaño relativo
    """
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    width = x2 - x1
    height = y2 - y1
    
    # Calcular tamaño relativo (área del bbox / área del frame)
    bbox_area = width * height
    frame_area = frame_width * frame_height
    relative_size = bbox_area / frame_area if frame_area > 0 else 0
    
    return {
        'x_center': center_x,
        'y_center': center_y,
        'width': width,
        'height': height,
        'relative_size': relative_size
    }


def calculate_proximity(relative_size: float, frame_width: int, frame_height: int) -> str:
    """
    Calcula la proximidad estimada basada en el tamaño relativo del objeto.
    
    Args:
        relative_size: Tamaño relativo del objeto (0-1)
        frame_width: Ancho del frame
        frame_height: Alto del frame
        
    Returns:
        'close', 'medium' o 'far'
    """
    # Heurística: objetos más grandes están más cerca
    # Ajustar umbrales para que sea más fácil detectar objetos cercanos
    if relative_size > 0.08:  # Más del 8% del frame (más sensible)
        return 'close'
    elif relative_size > 0.04:  # Entre 4% y 8%
        return 'medium'
    else:  # Menos del 4%
        return 'far'


def is_center_zone(x_center: float, y_center: float, frame_width: int, frame_height: int) -> bool:
    """
    Determina si un objeto está en la zona central (más peligrosa).
    
    Args:
        x_center: Coordenada X del centro
        y_center: Coordenada Y del centro
        frame_width: Ancho del frame
        frame_height: Alto del frame
        
    Returns:
        True si está en la zona central
    """
    center_x_threshold = frame_width * 0.4  # 40% desde cada lado
    center_y_threshold = frame_height * 0.4
    
    x_in_center = (frame_width * 0.3) < x_center < (frame_width * 0.7)
    y_in_center = (frame_height * 0.3) < y_center < (frame_height * 0.7)
    
    return x_in_center and y_in_center


def validate_camera_access(camera_index: int = 0) -> Tuple[bool, str]:
    """
    Valida si la cámara está disponible y accesible.
    
    Args:
        camera_index: Índice de la cámara a validar
        
    Returns:
        Tuple (éxito, mensaje)
    """
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



