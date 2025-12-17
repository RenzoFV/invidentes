# 📥 Guía de Instalación de OLLAMA

OLLAMA es necesario para generar descripciones naturales en español. Sin embargo, el sistema puede funcionar sin él usando descripciones básicas.

## 🚀 Instalación Rápida

### Windows

1. **Descargar OLLAMA:**
   - Ve a [https://ollama.ai/download](https://ollama.ai/download)
   - Descarga el instalador para Windows
   - Ejecuta el archivo `.exe` descargado

2. **Verificar instalación:**
   ```bash
   ollama --version
   ```

3. **Iniciar OLLAMA:**
   ```bash
   ollama serve
   ```
   Deja esta terminal abierta mientras usas la aplicación.

4. **Descargar modelo (en otra terminal):**
   ```bash
   ollama pull llama3
   ```
   O para mejor soporte en español:
   ```bash
   ollama pull llama3.2
   ```

### Linux

```bash
# Instalar OLLAMA
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar OLLAMA
ollama serve

# Descargar modelo (en otra terminal)
ollama pull llama3
```

### macOS

```bash
# Instalar con Homebrew
brew install ollama

# O descargar desde https://ollama.ai/download

# Iniciar OLLAMA
ollama serve

# Descargar modelo (en otra terminal)
ollama pull llama3
```

## ✅ Verificar que Funciona

Ejecuta el script de diagnóstico:

```bash
python check_ollama.py
```

Este script verificará:
- ✅ Si OLLAMA está instalado
- ✅ Si OLLAMA está corriendo
- ✅ Si el modelo está disponible

## 🔧 Solución de Problemas

### "OLLAMA no está en el PATH"

**Windows:**
- Reinicia la terminal después de instalar
- O agrega OLLAMA al PATH manualmente

**Linux/macOS:**
- Reinicia la terminal
- O ejecuta: `export PATH=$PATH:/usr/local/bin`

### "No se pudo conectar a OLLAMA"

1. Verifica que OLLAMA esté corriendo:
   ```bash
   ollama serve
   ```

2. Verifica que esté en el puerto correcto:
   - Por defecto: `http://localhost:11434`
   - Si cambias el puerto, actualiza `.env`:
     ```env
     OLLAMA_BASE_URL=http://localhost:TU_PUERTO
     ```

### "Modelo no encontrado"

Descarga el modelo:
```bash
ollama pull llama3
```

Para ver modelos disponibles:
```bash
ollama list
```

## 💡 Modo sin OLLAMA

Si no puedes instalar OLLAMA, el sistema funcionará con descripciones básicas:
- ✅ Detección de objetos funcionará
- ✅ Descripciones simples funcionarán
- ⚠️ Descripciones naturales y contextuales NO estarán disponibles

El sistema mostrará: "⚠️ OLLAMA no disponible. Se usará modo simple."

## 📝 Notas

- OLLAMA debe estar corriendo mientras usas la aplicación
- El primer uso puede ser lento mientras descarga el modelo
- Los modelos ocupan espacio (llama3 ~4.7GB)
- Puedes usar modelos más pequeños si tienes poco espacio:
  ```bash
  ollama pull llama3.2:1b  # Versión más pequeña
  ```

