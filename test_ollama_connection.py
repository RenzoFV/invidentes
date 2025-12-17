"""
Script rápido para verificar si OLLAMA está corriendo y accesible.
"""

import requests
import json

def test_ollama():
    """Prueba la conexión con OLLAMA."""
    base_url = "http://localhost:11434"
    
    print("🔍 Verificando conexión con OLLAMA...\n")
    
    try:
        # Probar conexión básica
        print(f"1. Probando conexión a {base_url}...")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print("   ✅ OLLAMA está corriendo y respondiendo\n")
            
            # Listar modelos
            data = response.json()
            models = data.get('models', [])
            
            if models:
                print("2. Modelos disponibles:")
                for model in models:
                    name = model.get('name', 'desconocido')
                    print(f"   ✅ {name}")
                
                # Verificar si llama3 está disponible
                model_names = [m.get('name', '') for m in models]
                has_llama3 = any('llama3' in name for name in model_names)
                
                print()
                if has_llama3:
                    print("✅ ¡Todo está listo! El modelo llama3 está disponible.")
                    print("   Puedes ejecutar la aplicación ahora.")
                else:
                    print("⚠️ El modelo llama3 no está disponible.")
                    print("   Descárgalo con: ollama pull llama3")
            else:
                print("⚠️ No hay modelos instalados.")
                print("   Descarga un modelo con: ollama pull llama3")
            
            return True
        else:
            print(f"   ❌ OLLAMA respondió con código {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ No se pudo conectar a OLLAMA")
        print("\n   El error 'bind: Only one usage' significa que:")
        print("   - OLLAMA ya está corriendo (esto es bueno)")
        print("   - Pero no está respondiendo en el puerto 11434")
        print("\n   Intenta:")
        print("   1. Reiniciar OLLAMA desde el menú de Windows")
        print("   2. O verificar si hay un firewall bloqueando")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_ollama()

