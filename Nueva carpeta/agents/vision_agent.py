"""
Agente de Visión: Detección de objetos usando YOLO con cálculo de proximidad.
"""

import logging
import cv2
import numpy as np
from typing import List, Dict, Optional
from ultralytics import YOLO
from config import (
    YOLO_MODEL, YOLO_CONFIDENCE_THRESHOLD,
    YOLO_PROCESS_EVERY_N_FRAMES, YOLO_IMG_SIZE,
    OBSTACLE_CLOSE_DISTANCE, OBSTACLE_MEDIUM_DISTANCE, OBSTACLE_FAR_DISTANCE
)
from utils.helpers import calculate_bbox_position, calculate_proximity, is_center_zone

logger = logging.getLogger(__name__)


class VisionAgent:
    """Agente especializado en detección de objetos usando YOLO con cálculo de proximidad."""
    
    def __init__(self, model_path: str = None, confidence: float = None):
        """
        Inicializa el agente de visión.
        
        Args:
            model_path: Ruta al modelo YOLO
            confidence: Umbral de confianza para detecciones
        """
        self.model_path = model_path or YOLO_MODEL
        self.confidence_threshold = confidence or YOLO_CONFIDENCE_THRESHOLD
        self.process_every_n_frames = YOLO_PROCESS_EVERY_N_FRAMES
        self.img_size = YOLO_IMG_SIZE
        self.frame_count = 0
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo YOLO."""
        try:
            logger.info(f"Cargando modelo YOLO: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("Modelo YOLO cargado correctamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo YOLO: {e}")
            raise
    
    def detect_objects(
        self, 
        frame: np.ndarray,
        force_process: bool = False
    ) -> List[Dict]:
        """
        Detecta objetos en un frame de video con cálculo de proximidad.
        
        Args:
            frame: Frame de video (numpy array)
            force_process: Si es True, procesa sin importar el contador
            
        Returns:
            Lista de objetos detectados con información estructurada incluyendo proximidad
        """
        if self.model is None:
            logger.error("Modelo YOLO no está cargado")
            return []
        
        # Optimización: procesar solo cada N frames
        self.frame_count += 1
        if not force_process and self.frame_count % self.process_every_n_frames != 0:
            return []
        
        try:
            # Redimensionar frame para velocidad (opcional, YOLO lo hace internamente)
            # Pero podemos hacerlo aquí para más control
            original_height, original_width = frame.shape[:2]
            
            # Ejecutar detección con tamaño optimizado
            results = self.model(
                frame, 
                conf=self.confidence_threshold, 
                imgsz=self.img_size,
                verbose=False
            )
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                
                # Procesar cada detección
                if result.boxes is not None:
                    for box in result.boxes:
                        # Obtener información del bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Obtener nombre de la clase
                        class_name = self.model.names[class_id]
                        
                        # Calcular posición y tamaño relativo
                        bbox_info = calculate_bbox_position(
                            x1, y1, x2, y2, original_width, original_height
                        )
                        
                        # Calcular proximidad basada en tamaño relativo
                        relative_size = bbox_info['relative_size']
                        proximity = calculate_proximity(relative_size, original_width, original_height)
                        
                        # Determinar si está en zona central (más peligroso)
                        is_center = is_center_zone(
                            bbox_info['x_center'],
                            bbox_info['y_center'],
                            original_width,
                            original_height
                        )
                        
                        # Filtrar por relevancia (objetos comunes en entornos)
                        if self._is_relevant_object(class_name, confidence):
                            detection = {
                                'name': class_name,
                                'confidence': confidence,
                                'class_id': class_id,
                                'bbox': {
                                    'x1': float(x1),
                                    'y1': float(y1),
                                    'x2': float(x2),
                                    'y2': float(y2),
                                    **bbox_info
                                },
                                'proximity': proximity,
                                'is_center': is_center,
                                'relative_size': relative_size
                            }
                            detections.append(detection)
            
            # Ordenar por prioridad: primero por zona central, luego por proximidad, luego por confianza
            detections.sort(
                key=lambda x: (
                    not x['is_center'],  # Centro primero (False < True, pero queremos True primero)
                    x['proximity'] != 'close',  # Cercanos primero
                    x['proximity'] != 'medium',
                    -x['confidence']  # Mayor confianza primero
                )
            )
            
            # Limitar número de detecciones para evitar sobrecarga
            max_detections = 10
            detections = detections[:max_detections]
            
            logger.debug(f"Detectados {len(detections)} objetos")
            return detections
            
        except Exception as e:
            logger.error(f"Error en detección de objetos: {e}")
            return []
    
    def _is_relevant_object(self, class_name: str, confidence: float) -> bool:
        """
        Determina si un objeto es relevante como obstáculo.
        
        Args:
            class_name: Nombre de la clase detectada
            confidence: Nivel de confianza
            
        Returns:
            True si el objeto es relevante como obstáculo
        """
        # Objetos muy relevantes para navegación y seguridad (obstáculos comunes)
        high_priority = [
            'person', 'chair', 'table', 'door', 'stairs', 
            'car', 'bus', 'truck', 'bicycle', 'motorcycle',
            'dog', 'cat', 'backpack', 'handbag', 'umbrella',
            'couch', 'bed', 'dining table', 'toilet', 'tv',
            'bottle', 'phone', 'cell phone', 'mobile phone'  # Agregar objetos comunes
        ]
        
        # Objetos de menor prioridad pero aún útiles
        medium_priority = [
            'cup', 'book', 'laptop', 
            'keyboard', 'mouse', 'vase', 'bowl',
            'remote', 'clock', 'scissors', 'toothbrush'
        ]
        
        class_lower = class_name.lower()
        
        # Si está en alta prioridad, siempre incluirlo si confianza > 0.4
        if class_lower in high_priority:
            return confidence >= 0.4
        
        # Si está en media prioridad, requerir mayor confianza
        if class_lower in medium_priority:
            return confidence >= 0.6
        
        # Otros objetos solo si confianza muy alta
        return confidence >= 0.7
    
    def get_obstacle_type(self, class_name: str) -> str:
        """
        Clasifica el tipo de obstáculo.
        
        Args:
            class_name: Nombre de la clase detectada
            
        Returns:
            Tipo de obstáculo: 'person', 'vehicle', 'furniture', 'object'
        """
        class_lower = class_name.lower()
        
        if class_lower == 'person':
            return 'person'
        elif class_lower in ['car', 'bus', 'truck', 'motorcycle', 'bicycle']:
            return 'vehicle'
        elif class_lower in ['chair', 'table', 'couch', 'bed', 'door', 'stairs']:
            return 'furniture'
        else:
            return 'object'
    
    def get_model_info(self) -> Dict:
        """
        Obtiene información sobre el modelo cargado.
        
        Returns:
            Diccionario con información del modelo
        """
        if self.model is None:
            return {'status': 'not_loaded'}
        
        return {
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold,
            'img_size': self.img_size,
            'classes': len(self.model.names) if hasattr(self.model, 'names') else 0,
            'status': 'loaded'
        }
    
    def reset_frame_count(self):
        """Reinicia el contador de frames."""
        self.frame_count = 0



