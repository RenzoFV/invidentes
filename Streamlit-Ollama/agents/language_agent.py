"""
Agente de Lenguaje: Generación de descripciones naturales usando OLLAMA.
"""

import logging
import hashlib
import json
import requests
from typing import List, Dict, Optional
from ollama import Client
from config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_DESCRIPTION_LENGTH,
    CACHE_DESCRIPTIONS
)
from modules.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class LanguageAgent:
    """Agente especializado en generar descripciones naturales en español."""
    
    def __init__(
        self, 
        base_url: str = None, 
        model: str = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Inicializa el agente de lenguaje.
        
        Args:
            base_url: URL base de OLLAMA
            model: Nombre del modelo a usar
            db_manager: Instancia de DatabaseManager para cache
        """
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or OLLAMA_MODEL
        self.db_manager = db_manager
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de OLLAMA."""
        try:
            self.client = Client(host=self.base_url)
            logger.info(f"Cliente OLLAMA inicializado: {self.base_url}")
        except Exception as e:
            logger.error(f"Error al inicializar cliente OLLAMA: {e}")
            self.client = None
    
    def _create_hash_from_detections(self, detections: List[Dict]) -> str:
        """
        Crea un hash único a partir de las detecciones para cache.
        
        Args:
            detections: Lista de objetos detectados
            
        Returns:
            Hash MD5 de las detecciones
        """
        # Normalizar detecciones (solo nombres y posiciones aproximadas)
        normalized = []
        for det in detections:
            normalized.append({
                'name': det.get('name', ''),
                'x_center': round(det.get('bbox', {}).get('x_center', 0) / 100),
                'y_center': round(det.get('bbox', {}).get('y_center', 0) / 100)
            })
        
        # Ordenar para consistencia
        normalized.sort(key=lambda x: (x['name'], x['x_center'], x['y_center']))
        
        # Crear hash
        detections_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(detections_str.encode()).hexdigest()
    
    def _build_prompt(self, detections: List[Dict], detailed: bool = False) -> str:
        """
        Construye el prompt para OLLAMA.
        
        Args:
            detections: Lista de objetos detectados
            detailed: Si es True, solicita descripción más detallada
            
        Returns:
            Prompt formateado
        """
        if not detections:
            return "No se detectaron objetos en el entorno. Genera una descripción breve indicando esto."
        
        # Formatear detecciones para el prompt
        objects_list = []
        for det in detections:
            name = det.get('name', 'objeto')
            confidence = det.get('confidence', 0)
            bbox = det.get('bbox', {})
            
            x_center = bbox.get('x_center', 0)
            y_center = bbox.get('y_center', 0)
            
            # Determinar posición relativa
            if x_center < 213:  # ~33% del ancho (640px)
                pos_h = "izquierda"
            elif x_center > 427:  # ~67% del ancho
                pos_h = "derecha"
            else:
                pos_h = "centro"
            
            if y_center < 160:  # ~33% del alto (480px)
                pos_v = "arriba"
            elif y_center > 320:  # ~67% del alto
                pos_v = "abajo"
            else:
                pos_v = "medio"
            
            # Manejar objetos de audio (ruido) de forma especial
            if name == 'ruido' and 'audio_info' in det:
                audio_info = det.get('audio_info', {})
                level = audio_info.get('level', 'moderado')
                objects_list.append(
                    f"- Ruido {level} detectado en el entorno"
                )
            else:
                objects_list.append(
                    f"- {name} en {pos_h}-{pos_v} (confianza: {confidence:.0%})"
                )
        
        objects_text = "\n".join(objects_list)
        
        if detailed:
            prompt = f"""Eres un asistente de voz para personas invidentes. Describe el entorno de forma clara, natural y detallada en español.

Objetos detectados:
{objects_text}

Genera una descripción natural y detallada en español (máximo {MAX_DESCRIPTION_LENGTH} caracteres) que ayude a una persona invidente a entender su entorno. Incluye:
- Qué objetos hay y dónde están ubicados
- Distancias relativas si es posible
- Cualquier información relevante para navegación o seguridad

Descripción:"""
        else:
            prompt = f"""Eres un asistente de voz para personas invidentes. Describe el entorno de forma clara y concisa en español.

Objetos detectados:
{objects_text}

Genera una descripción breve y natural en español (máximo {MAX_DESCRIPTION_LENGTH} caracteres) que ayude a una persona invidente a entender su entorno. Sé conciso pero informativo.

Descripción:"""
        
        return prompt
    
    def generate_description(
        self, 
        detections: List[Dict],
        detailed: bool = False,
        use_cache: bool = True
    ) -> str:
        """
        Genera una descripción natural a partir de las detecciones.
        
        Args:
            detections: Lista de objetos detectados
            detailed: Si es True, genera descripción más detallada
            use_cache: Si es True, intenta usar cache
            
        Returns:
            Descripción generada en español
        """
        # Verificar cache si está habilitado
        if use_cache and CACHE_DESCRIPTIONS and self.db_manager:
            hash_detections = self._create_hash_from_detections(detections)
            cached = self.db_manager.get_cached_description(hash_detections)
            if cached:
                logger.debug("Descripción obtenida del cache")
                return cached
        
        # Si no hay detecciones, retornar mensaje simple
        if not detections:
            return "No se detectaron objetos en el entorno cercano."
        
        # Si OLLAMA no está disponible, usar descripción simple
        if self.client is None:
            logger.warning("OLLAMA no disponible, usando descripción simple")
            return self._generate_simple_description(detections)
        
        try:
            # Construir prompt
            prompt = self._build_prompt(detections, detailed)
            
            # Llamar a OLLAMA
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'max_tokens': 300,  # Aumentado para descripciones más completas
                    'top_p': 0.9
                }
            )
            
            # Extraer descripción
            description = response.get('response', '').strip()
            
            # Limpiar y validar descripción
            description = self._clean_description(description)
            
            # Guardar en cache si está habilitado
            if use_cache and CACHE_DESCRIPTIONS and self.db_manager:
                hash_detections = self._create_hash_from_detections(detections)
                self.db_manager.cache_description(hash_detections, description)
            
            logger.debug(f"Descripción generada: {description[:50]}...")
            return description
            
        except requests.exceptions.ConnectionError:
            logger.error("No se pudo conectar a OLLAMA")
            return self._generate_simple_description(detections)
        except Exception as e:
            logger.error(f"Error al generar descripción: {e}")
            return self._generate_simple_description(detections)
    
    def _generate_simple_description(self, detections: List[Dict]) -> str:
        """
        Genera una descripción simple sin OLLAMA (fallback).
        
        Args:
            detections: Lista de objetos detectados
            
        Returns:
            Descripción simple formateada
        """
        from utils.helpers import format_spatial_description
        return format_spatial_description(detections)
    
    def _clean_description(self, description: str) -> str:
        """
        Limpia y valida la descripción generada.
        
        Args:
            description: Descripción cruda
            
        Returns:
            Descripción limpia
        """
        # Remover saltos de línea múltiples
        description = ' '.join(description.split())
        
        # Limitar longitud solo si es extremadamente larga (evitar cortes abruptos)
        # Intentar cortar en un punto final para mantener coherencia
        if len(description) > MAX_DESCRIPTION_LENGTH:
            # Buscar el último punto antes del límite
            truncated = description[:MAX_DESCRIPTION_LENGTH]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            
            # Usar el último signo de puntuación encontrado
            last_punctuation = max(last_period, last_exclamation, last_question)
            
            if last_punctuation > MAX_DESCRIPTION_LENGTH * 0.7:  # Si hay puntuación cerca del límite
                description = description[:last_punctuation + 1]
            else:
                # Si no hay puntuación cercana, cortar en la última palabra completa
                description = truncated.rsplit(' ', 1)[0] + "."
        
        # Asegurar que termine con punto
        if description and not description.endswith(('.', '!', '?')):
            description += "."
        
        return description.strip()
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con OLLAMA.
        
        Returns:
            True si la conexión es exitosa
        """
        if self.client is None:
            return False
        
        try:
            # Intentar listar modelos
            models = self.client.list()
            logger.info("Conexión con OLLAMA exitosa")
            return True
        except Exception as e:
            logger.error(f"Error al probar conexión OLLAMA: {e}")
            return False

