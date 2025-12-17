"""
Gestión de base de datos PostgreSQL/Supabase para perfiles de usuario,
historial de detecciones y cache de descripciones.
Soporta conexión directa PostgreSQL y cliente Supabase (Project URL + API Key).
"""

import logging
import json
from typing import Dict, List, Optional
from config import (
    DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, USE_SUPABASE_CLIENT, LOG_LEVEL
)

logger = logging.getLogger(__name__)

# Importar según el método de conexión
if USE_SUPABASE_CLIENT:
    try:
        from supabase import create_client, Client
        SUPABASE_AVAILABLE = True
    except ImportError:
        SUPABASE_AVAILABLE = False
        logger.warning("Cliente Supabase no disponible. Instala: pip install supabase")
else:
    SUPABASE_AVAILABLE = False
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    import urllib.parse as urlparse


class DatabaseManager:
    """Gestor de conexiones y operaciones con PostgreSQL/Supabase."""
    
    def __init__(self):
        """Inicializa la conexión y crea las tablas si no existen."""
        self.supabase_client = None
        self.connection_pool = None
        self.use_supabase = USE_SUPABASE_CLIENT and SUPABASE_AVAILABLE
        
        if self.use_supabase:
            self._initialize_supabase()
        else:
            self._initialize_postgres()
        
        self._create_tables()
    
    def _initialize_supabase(self):
        """Inicializa el cliente de Supabase."""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
            
            self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Cliente Supabase inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar cliente Supabase: {e}")
            self.supabase_client = None
            self.use_supabase = False
    
    def _initialize_postgres(self):
        """Inicializa el pool de conexiones PostgreSQL."""
        try:
            if not DATABASE_URL:
                raise ValueError("DATABASE_URL debe estar configurado")
            
            # Verificar si es Supabase
            is_supabase = 'supabase.co' in DATABASE_URL or 'supabase.com' in DATABASE_URL
            
            if is_supabase:
                # Para Supabase, parsear URL y agregar SSL
                parsed = urlparse.urlparse(DATABASE_URL)
                
                # Construir parámetros de conexión
                conn_params = {
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'database': parsed.path[1:] if parsed.path else 'postgres',
                    'user': parsed.username,
                    'password': parsed.password,
                    'sslmode': 'require'  # Supabase requiere SSL
                }
                
                # Detectar tipo de conexión
                if 'pooler' in parsed.hostname:
                    logger.info("Conectando a Supabase usando Connection Pooling")
                elif 'db.' in parsed.hostname:
                    logger.info("Conectando a Supabase usando conexión directa")
                else:
                    logger.info("Conectando a Supabase")
                
                # Crear pool de conexiones con parámetros
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10, **conn_params
                )
            else:
                # Para PostgreSQL local o otras conexiones, usar URL directa
                logger.info("Conectando a PostgreSQL local o remoto")
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10, DATABASE_URL
                )
            
            if self.connection_pool:
                logger.info("Pool de conexiones PostgreSQL inicializado correctamente")
            else:
                logger.error("Error al crear el pool de conexiones")
                self.connection_pool = None
                
        except Exception as e:
            logger.error(f"Error al inicializar pool de conexiones: {e}")
            # Fallback: intentar conexión directa con URL
            try:
                logger.info("Intentando conexión directa con URL...")
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10, DATABASE_URL
                )
                if self.connection_pool:
                    logger.info("Pool de conexiones inicializado con URL directa")
                else:
                    self.connection_pool = None
            except Exception as e2:
                logger.error(f"Error en fallback de conexión: {e2}")
                self.connection_pool = None
    
    def _get_connection(self):
        """Obtiene una conexión del pool (solo para PostgreSQL directo)."""
        if self.connection_pool:
            return self.connection_pool.getconn()
        else:
            raise Exception("Pool de conexiones no disponible")
    
    def _return_connection(self, conn):
        """Devuelve una conexión al pool (solo para PostgreSQL directo)."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def _create_tables(self):
        """Crea las tablas necesarias si no existen."""
        if self.use_supabase:
            # Para Supabase, usar RPC o ejecutar SQL directamente
            # Nota: El cliente de Supabase no puede crear tablas directamente
            # Necesitamos usar la conexión PostgreSQL o crear las tablas manualmente
            logger.warning("Para crear tablas en Supabase, úsalas desde el dashboard o SQL Editor")
            logger.info("Las tablas se crearán automáticamente en el primer uso si no existen")
            return
        
        # Para PostgreSQL directo, crear tablas
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Tabla de usuarios/perfiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE,
                    preferencias_tts JSONB DEFAULT '{}',
                    velocidad_habla INTEGER DEFAULT 150,
                    volumen REAL DEFAULT 0.8,
                    modo_detallado BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de historial de detecciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detecciones (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    objetos_detectados JSONB,
                    descripcion_generada TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de cache de descripciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_descripciones (
                    id SERIAL PRIMARY KEY,
                    hash_objetos VARCHAR(64) UNIQUE,
                    descripcion TEXT,
                    uso_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para optimización
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detecciones_usuario 
                ON detecciones(usuario_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detecciones_timestamp 
                ON detecciones(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_hash 
                ON cache_descripciones(hash_objetos)
            """)
            
            conn.commit()
            logger.info("Tablas de base de datos creadas/verificadas correctamente")
            
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self._return_connection(conn)
    
    def create_or_get_user(self, nombre: str = "default") -> Dict:
        """
        Crea o obtiene un perfil de usuario.
        
        Args:
            nombre: Nombre del usuario
            
        Returns:
            Diccionario con los datos del usuario
        """
        if self.use_supabase:
            return self._create_or_get_user_supabase(nombre)
        else:
            return self._create_or_get_user_postgres(nombre)
    
    def _create_or_get_user_supabase(self, nombre: str) -> Dict:
        """Crea o obtiene usuario usando cliente Supabase."""
        try:
            # Intentar obtener usuario existente
            response = self.supabase_client.table('usuarios').select('*').eq('nombre', nombre).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            # Crear nuevo usuario
            new_user = {
                'nombre': nombre,
                'velocidad_habla': 150,
                'volumen': 0.8,
                'modo_detallado': False,
                'preferencias_tts': {}
            }
            
            response = self.supabase_client.table('usuarios').insert(new_user).execute()
            logger.info(f"Usuario '{nombre}' creado")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error al crear/obtener usuario: {e}")
            return {}
    
    def _create_or_get_user_postgres(self, nombre: str) -> Dict:
        """Crea o obtiene usuario usando PostgreSQL directo."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Intentar obtener usuario existente
            cursor.execute(
                "SELECT * FROM usuarios WHERE nombre = %s",
                (nombre,)
            )
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # Crear nuevo usuario
            cursor.execute("""
                INSERT INTO usuarios (nombre)
                VALUES (%s)
                RETURNING *
            """, (nombre,))
            
            user = cursor.fetchone()
            conn.commit()
            logger.info(f"Usuario '{nombre}' creado")
            return dict(user)
            
        except Exception as e:
            logger.error(f"Error al crear/obtener usuario: {e}")
            if conn:
                conn.rollback()
            return {}
        finally:
            if conn:
                self._return_connection(conn)
    
    def update_user_preferences(
        self, 
        usuario_id: int, 
        preferencias: Dict
    ) -> bool:
        """
        Actualiza las preferencias de un usuario.
        
        Args:
            usuario_id: ID del usuario
            preferencias: Diccionario con preferencias a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if self.use_supabase:
            return self._update_user_preferences_supabase(usuario_id, preferencias)
        else:
            return self._update_user_preferences_postgres(usuario_id, preferencias)
    
    def _update_user_preferences_supabase(self, usuario_id: int, preferencias: Dict) -> bool:
        """Actualiza preferencias usando cliente Supabase."""
        try:
            # Preparar datos para actualizar
            update_data = {}
            if 'velocidad_habla' in preferencias:
                update_data['velocidad_habla'] = preferencias['velocidad_habla']
            if 'volumen' in preferencias:
                update_data['volumen'] = preferencias['volumen']
            if 'modo_detallado' in preferencias:
                update_data['modo_detallado'] = preferencias['modo_detallado']
            if 'preferencias_tts' in preferencias:
                update_data['preferencias_tts'] = preferencias['preferencias_tts']
            
            if update_data:
                response = self.supabase_client.table('usuarios').update(update_data).eq('id', usuario_id).execute()
                logger.info(f"Preferencias del usuario {usuario_id} actualizadas")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error al actualizar preferencias: {e}")
            return False
    
    def _update_user_preferences_postgres(self, usuario_id: int, preferencias: Dict) -> bool:
        """Actualiza preferencias usando PostgreSQL directo."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            updates = []
            values = []
            
            if 'velocidad_habla' in preferencias:
                updates.append("velocidad_habla = %s")
                values.append(preferencias['velocidad_habla'])
            
            if 'volumen' in preferencias:
                updates.append("volumen = %s")
                values.append(preferencias['volumen'])
            
            if 'modo_detallado' in preferencias:
                updates.append("modo_detallado = %s")
                values.append(preferencias['modo_detallado'])
            
            if 'preferencias_tts' in preferencias:
                updates.append("preferencias_tts = %s")
                values.append(preferencias['preferencias_tts'])
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(usuario_id)
                
                query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, values)
                conn.commit()
                logger.info(f"Preferencias del usuario {usuario_id} actualizadas")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error al actualizar preferencias: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._return_connection(conn)
    
    def save_detection(
        self, 
        usuario_id: int, 
        objetos_detectados: List[Dict],
        descripcion_generada: str
    ) -> bool:
        """
        Guarda una detección en el historial.
        
        Args:
            usuario_id: ID del usuario
            objetos_detectados: Lista de objetos detectados
            descripcion_generada: Descripción generada por el agente de lenguaje
            
        Returns:
            True si se guardó correctamente
        """
        if self.use_supabase:
            return self._save_detection_supabase(usuario_id, objetos_detectados, descripcion_generada)
        else:
            return self._save_detection_postgres(usuario_id, objetos_detectados, descripcion_generada)
    
    def _save_detection_supabase(self, usuario_id: int, objetos_detectados: List[Dict], descripcion_generada: str) -> bool:
        """Guarda detección usando cliente Supabase."""
        try:
            # Convertir objetos numpy a tipos nativos de Python para serialización JSON
            from utils.json_helpers import convert_to_serializable
            
            objetos_serializables = convert_to_serializable(objetos_detectados)
            
            detection_data = {
                'usuario_id': usuario_id,
                'objetos_detectados': objetos_serializables,
                'descripcion_generada': descripcion_generada
            }
            
            response = self.supabase_client.table('detecciones').insert(detection_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar detección: {e}")
            return False
    
    def _save_detection_postgres(self, usuario_id: int, objetos_detectados: List[Dict], descripcion_generada: str) -> bool:
        """Guarda detección usando PostgreSQL directo."""
        conn = None
        try:
            from utils.json_helpers import safe_json_dumps
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Usar safe_json_dumps para convertir tipos numpy
            objetos_json = safe_json_dumps(objetos_detectados)
            
            cursor.execute("""
                INSERT INTO detecciones (usuario_id, objetos_detectados, descripcion_generada)
                VALUES (%s, %s, %s)
            """, (usuario_id, objetos_json, descripcion_generada))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar detección: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_cached_description(self, hash_objetos: str) -> Optional[str]:
        """
        Obtiene una descripción del cache si existe.
        
        Args:
            hash_objetos: Hash de los objetos detectados
            
        Returns:
            Descripción cacheada o None
        """
        if self.use_supabase:
            return self._get_cached_description_supabase(hash_objetos)
        else:
            return self._get_cached_description_postgres(hash_objetos)
    
    def _get_cached_description_supabase(self, hash_objetos: str) -> Optional[str]:
        """Obtiene descripción cacheada usando cliente Supabase."""
        try:
            response = self.supabase_client.table('cache_descripciones').select('*').eq('hash_objetos', hash_objetos).execute()
            
            if response.data and len(response.data) > 0:
                cached = response.data[0]
                # Actualizar contador y timestamp
                new_count = cached.get('uso_count', 1) + 1
                self.supabase_client.table('cache_descripciones').update({
                    'uso_count': new_count
                }).eq('hash_objetos', hash_objetos).execute()
                
                return cached['descripcion']
            
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener descripción cacheada: {e}")
            return None
    
    def _get_cached_description_postgres(self, hash_objetos: str) -> Optional[str]:
        """Obtiene descripción cacheada usando PostgreSQL directo."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT descripcion FROM cache_descripciones
                WHERE hash_objetos = %s
            """, (hash_objetos,))
            
            result = cursor.fetchone()
            
            if result:
                # Actualizar contador y timestamp
                cursor.execute("""
                    UPDATE cache_descripciones
                    SET uso_count = uso_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE hash_objetos = %s
                """, (hash_objetos,))
                conn.commit()
                return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener descripción cacheada: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self._return_connection(conn)
    
    def cache_description(self, hash_objetos: str, descripcion: str) -> bool:
        """
        Guarda una descripción en el cache.
        
        Args:
            hash_objetos: Hash de los objetos detectados
            descripcion: Descripción a cachear
            
        Returns:
            True si se guardó correctamente
        """
        if self.use_supabase:
            return self._cache_description_supabase(hash_objetos, descripcion)
        else:
            return self._cache_description_postgres(hash_objetos, descripcion)
    
    def _cache_description_supabase(self, hash_objetos: str, descripcion: str) -> bool:
        """Cachea descripción usando cliente Supabase."""
        try:
            # Verificar si ya existe
            existing = self.supabase_client.table('cache_descripciones').select('uso_count').eq('hash_objetos', hash_objetos).execute()
            
            if existing.data and len(existing.data) > 0:
                # Actualizar existente
                new_count = existing.data[0].get('uso_count', 1) + 1
                self.supabase_client.table('cache_descripciones').update({
                    'descripcion': descripcion,
                    'uso_count': new_count
                }).eq('hash_objetos', hash_objetos).execute()
            else:
                # Insertar nuevo
                cache_data = {
                    'hash_objetos': hash_objetos,
                    'descripcion': descripcion,
                    'uso_count': 1
                }
                self.supabase_client.table('cache_descripciones').insert(cache_data).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al cachear descripción: {e}")
            return False
    
    def _cache_description_postgres(self, hash_objetos: str, descripcion: str) -> bool:
        """Cachea descripción usando PostgreSQL directo."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cache_descripciones (hash_objetos, descripcion)
                VALUES (%s, %s)
                ON CONFLICT (hash_objetos) 
                DO UPDATE SET 
                    descripcion = EXCLUDED.descripcion,
                    uso_count = cache_descripciones.uso_count + 1,
                    last_used = CURRENT_TIMESTAMP
            """, (hash_objetos, descripcion))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error al cachear descripción: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._return_connection(conn)
    
    def close(self):
        """Cierra las conexiones."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Pool de conexiones cerrado")
