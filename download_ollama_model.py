"""
Script para descargar el modelo de OLLAMA usando la API directamente.
"""

import requests
import json
import time

def download_model(model_name="llama3"):
    """Descarga un modelo de OLLAMA usando la API."""
    base_url = "http://localhost:11434"
    
    print(f"📥 Descargando modelo '{model_name}'...")
    print("   Esto puede tardar varios minutos (el modelo es ~4.7GB)\n")
    
    try:
        # Iniciar descarga
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"❌ Error al iniciar descarga: {response.status_code}")
            return False
        
        # Procesar respuesta stream
        print("Progreso:")
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    
                    if 'status' in data:
                        status = data.get('status', '')
                        if 'pulling' in status.lower() or 'downloading' in status.lower():
                            print(f"   {status}")
                        elif 'verifying' in status.lower():
                            print(f"   {status}")
                        elif 'complete' in status.lower() or 'success' in status.lower():
                            print(f"   ✅ {status}")
                            break
                    
                    if 'error' in data:
                        print(f"   ❌ Error: {data['error']}")
                        return False
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"\n✅ Modelo '{model_name}' descargado correctamente!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar a OLLAMA")
        print("   Asegúrate de que OLLAMA esté corriendo")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_model(model_name="llama3"):
    """Verifica si el modelo está disponible."""
    base_url = "http://localhost:11434"
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            if any(model_name in name for name in model_names):
                return True
        return False
    except:
        return False

if __name__ == "__main__":
    model = "llama3"
    
    print("🔍 Verificando si el modelo ya está instalado...\n")
    
    if verify_model(model):
        print(f"✅ El modelo '{model}' ya está instalado!")
        print("   Puedes ejecutar la aplicación ahora.")
    else:
        print(f"📥 El modelo '{model}' no está instalado.\n")
        download_model(model)
        
        # Verificar después de descargar
        print("\n🔍 Verificando instalación...")
        if verify_model(model):
            print("✅ ¡Modelo instalado correctamente!")
            print("   Puedes ejecutar la aplicación ahora.")
        else:
            print("⚠️ El modelo podría no estar completamente instalado.")
            print("   Intenta ejecutar la aplicación de todas formas.")

