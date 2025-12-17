# 🔧 Configuración de Supabase

Esta guía te ayudará a configurar Supabase como base de datos para el sistema de asistencia visual.

## 📋 Pasos para Configurar Supabase

### 1. Crear Cuenta y Proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea una cuenta (es gratis)
3. Crea un nuevo proyecto:
   - Haz clic en "New Project"
   - Elige un nombre para tu proyecto
   - Elige una contraseña segura para la base de datos (guárdala bien)
   - Selecciona una región cercana
   - Espera a que se cree el proyecto (2-3 minutos)

### 2. Obtener Información de Conexión

Tienes **tres opciones** para configurar la conexión:

#### **Opción A: Cliente Supabase (Project URL + API Key) - RECOMENDADO ⭐**

Esta es la forma más fácil y recomendada:

1. En tu proyecto de Supabase, ve a **Settings** (⚙️) en el menú lateral
2. Selecciona **API** en el submenú
3. Encontrarás:
   - **Project URL**: `https://[tu-project-ref].supabase.co`
   - **anon public key**: La clave pública (recomendada para aplicaciones)
   - **service_role key**: La clave de servicio (solo para operaciones administrativas)

**Ventajas:**
- ✅ Más fácil de configurar
- ✅ No necesitas manejar conexiones SSL manualmente
- ✅ Usa la API REST de Supabase (más seguro)
- ✅ Funciona perfectamente con el cliente Python

#### **Opción B: URL Completa de Conexión PostgreSQL**

1. En tu proyecto de Supabase, ve a **Settings** (⚙️) en el menú lateral
2. Selecciona **Database** en el submenú
3. Desplázate hasta la sección **Connection string**
4. Selecciona la pestaña **URI** (Connection Pooling - recomendado)
5. Copia la URL completa

#### **Opción C: Componentes del Proyecto**

Si prefieres usar componentes separados, necesitas:
- **PROJECT_REF**: Lo encuentras en la URL de tu proyecto
- **Contraseña de Base de Datos**: La que configuraste al crear el proyecto
- **Región**: La región de tu proyecto

### 3. Configurar el Archivo .env

1. Copia `env_template.txt` a `.env`:
   ```bash
   cp env_template.txt .env
   ```

2. **Opción A - Cliente Supabase (Recomendado):**
   ```env
   SUPABASE_URL=https://tu-project-ref.supabase.co
   SUPABASE_KEY=tu_anon_key_aqui
   ```
   **⚠️ IMPORTANTE:** 
   - Usa la **anon public key** para aplicaciones normales
   - Solo usa **service_role key** si necesitas permisos administrativos
   - No compartas nunca tu service_role key

3. **Opción B - URL Completa:**
   ```env
   DATABASE_URL=postgresql://postgres.xxxxx:tu_contraseña@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

4. **Opción C - Componentes:**
   ```env
   SUPABASE_PROJECT_REF=tu_project_ref
   SUPABASE_DB_PASSWORD=tu_contraseña
   SUPABASE_REGION=us-east-1
   ```

### 4. Crear las Tablas en Supabase

**Si usas Opción A (Cliente Supabase):**

Las tablas se crearán automáticamente cuando las uses por primera vez, O puedes crearlas manualmente desde el SQL Editor de Supabase:

1. Ve a **SQL Editor** en el menú lateral de Supabase
2. Crea un nuevo query y ejecuta este SQL:

```sql
-- Tabla de usuarios/perfiles
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE,
    preferencias_tts JSONB DEFAULT '{}',
    velocidad_habla INTEGER DEFAULT 150,
    volumen REAL DEFAULT 0.8,
    modo_detallado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de detecciones
CREATE TABLE IF NOT EXISTS detecciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    objetos_detectados JSONB,
    descripcion_generada TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de cache de descripciones
CREATE TABLE IF NOT EXISTS cache_descripciones (
    id SERIAL PRIMARY KEY,
    hash_objetos VARCHAR(64) UNIQUE,
    descripcion TEXT,
    uso_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_detecciones_usuario ON detecciones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_detecciones_timestamp ON detecciones(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cache_hash ON cache_descripciones(hash_objetos);
```

**Si usas Opción B o C (PostgreSQL directo):**

Las tablas se crearán automáticamente al iniciar la aplicación.

### 5. Configurar Permisos (Solo para Opción A)

Si usas el cliente de Supabase, asegúrate de que las políticas RLS (Row Level Security) permitan las operaciones:

1. Ve a **Authentication** > **Policies** en Supabase
2. O desactiva RLS temporalmente para desarrollo (Settings > API > Disable RLS)

Para producción, configura políticas apropiadas.

### 6. Verificar la Conexión

1. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

2. Si hay errores de conexión, verifica:
   - Que la URL y API Key sean correctas (Opción A)
   - Que la URL de conexión sea correcta (Opción B/C)
   - Que las tablas existan en Supabase
   - Que el proyecto de Supabase esté activo

3. Puedes verificar las tablas en Supabase:
   - Ve a **Table Editor** en el menú lateral
   - Deberías ver las tablas: `usuarios`, `detecciones`, `cache_descripciones`

## 🔍 Verificar que Funciona

El sistema detectará automáticamente qué método de conexión estás usando:
- **Opción A**: Usa el cliente de Supabase (más seguro y fácil)
- **Opción B/C**: Usa conexión PostgreSQL directa con SSL automático

## 🛠️ Solución de Problemas

### Error: "Cliente Supabase no disponible"
- Instala el cliente: `pip install supabase`
- Verifica que `SUPABASE_URL` y `SUPABASE_KEY` estén configurados

### Error: "SSL connection required"
- El sistema debería detectar Supabase automáticamente y configurar SSL
- Si persiste, verifica que la URL contenga `supabase.co`

### Error: "password authentication failed"
- Verifica que la contraseña en la URL sea correcta (Opción B/C)
- O verifica que la API Key sea correcta (Opción A)

### Error: "relation does not exist"
- Las tablas no existen. Créalas manualmente desde SQL Editor (Opción A)
- O verifica que la conexión PostgreSQL funcione (Opción B/C)

### Error: "permission denied" (Opción A)
- Verifica las políticas RLS en Supabase
- O usa `service_role key` en lugar de `anon key` (solo para desarrollo)

## 📊 Ventajas de Cada Opción

### Opción A: Cliente Supabase ⭐
- ✅ Más fácil de configurar
- ✅ Más seguro (API REST)
- ✅ No necesitas manejar SSL manualmente
- ✅ Mejor para aplicaciones web
- ⚠️ Requiere crear tablas manualmente o usar RPC

### Opción B/C: PostgreSQL Directo
- ✅ Creación automática de tablas
- ✅ Control total sobre la conexión
- ✅ Compatible con herramientas PostgreSQL estándar
- ⚠️ Requiere manejar SSL manualmente

## 🔐 Seguridad

- **Nunca** compartas tu archivo `.env` o lo subas a Git
- Añade `.env` a tu `.gitignore`
- La API Key y URL contienen credenciales sensibles
- Para producción, usa variables de entorno del sistema
- Si comprometes tu API Key, puedes regenerarla en Supabase: Settings > API > Reset API keys

## 📝 Notas Importantes

- **Opción A (Cliente Supabase)** es la más recomendada para nuevas implementaciones
- El sistema detecta automáticamente qué método usar
- Puedes cambiar entre métodos simplemente actualizando `.env`
- Las tablas tienen la misma estructura independientemente del método usado

---

**Recomendación:** Usa **Opción A (Cliente Supabase)** para la mejor experiencia de desarrollo.
