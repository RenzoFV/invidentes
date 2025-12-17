"""
Script de diagnóstico para verificar la instalación y conexión de OLLAMA.
"""

import requests
import sys
import subprocess

def check_ollama_installed():
    """Verifica si OLLAMA está instalado."""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ OLLAMA está instalado: {result.stdout.strip()}")
            return True
        else:
            print("❌ OLLAMA no está instalado correctamente")
            return False
    except FileNotFoundError:
        print("❌ OLLAMA no está instalado o no está en el PATH")
        return False
    except Exception as e:
        print(f"❌ Error al verificar OLLAMA: {e}")
        return False

def check_ollama_running(base_url="http://localhost:11434"):
    """Verifica si OLLAMA está corriendo."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ OLLAMA está corriendo en {base_url}")
            return True
        else:
            print(f"⚠️ OLLAMA respondió con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a OLLAMA en {base_url}")
        print("   Asegúrate de que OLLAMA esté corriendo: ollama serve")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout al conectar con OLLAMA en {base_url}")
        return False
    except Exception as e:
        print(f"❌ Error al verificar OLLAMA: {e}")
        return False

def check_ollama_models(base_url="http://localhost:11434", model="llama3"):
    """Verifica si el modelo está disponible."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            print(f"\n📦 Modelos disponibles en OLLAMA:")
            if model_names:
                for m in model_names:
                    print(f"   - {m}")
            else:
                print("   (ningún modelo instalado)")
            
            # Verificar si el modelo específico está disponible
            if any(model in m for m in model_names):
                print(f"\n✅ Modelo '{model}' está disponible")
                return True
            else:
                print(f"\n⚠️ Modelo '{model}' NO está disponible")
                print(f"   Descárgalo con: ollama pull {model}")
                return False
        else:
            return False
    except Exception as e:
        print(f"❌ Error al verificar modelos: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones."""
    print("🔍 Verificando OLLAMA...\n")
    
    # Verificar instalación
    installed = check_ollama_installed()
    print()
    
    if not installed:
        print("\n📥 Para instalar OLLAMA:")
        print("   1. Visita: https://ollama.ai")
        print("   2. Descarga e instala OLLAMA para tu sistema operativo")
        print("   3. Reinicia la terminal después de instalar")
        return False
    
    # Verificar si está corriendo
    running = check_ollama_running()
    print()
    
    if not running:
        print("\n🚀 Para iniciar OLLAMA:")
        print("   Ejecuta en una terminal: ollama serve")
        print("   O inicia OLLAMA como servicio en segundo plano")
        return False
    
    # Verificar modelos
    models_ok = check_ollama_models()
    print()
    
    if not models_ok:
        print("\n📥 Para descargar el modelo:")
        print("   ollama pull llama3")
        print("   O para mejor soporte en español:")
        print("   ollama pull llama3.2")
        return False
    
    print("\n✅ ¡Todo está configurado correctamente!")
    print("   Puedes ejecutar la aplicación ahora.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

