"""
Script de prueba para verificar que el sistema de voz funcione.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules.voice_announcer import VoiceAnnouncer

print("=" * 60)
print("PRUEBA DEL SISTEMA DE VOZ")
print("=" * 60)
print()

# Crear instancia
print("1. Creando VoiceAnnouncer...")
announcer = VoiceAnnouncer()

print(f"   - Habilitado: {announcer.enabled}")
print(f"   - Motor: {announcer.engine_name}")
print(f"   - Engine disponible: {announcer.engine is not None}")
print()

if not announcer.enabled:
    print("❌ ERROR: El sistema de voz está deshabilitado")
    print("   Verifica que ENABLE_VOICE_DESCRIPTIONS=true en config.py")
    sys.exit(1)

if not announcer.engine:
    print("❌ ERROR: El motor de voz no está inicializado")
    sys.exit(1)

# Probar diferentes mensajes
print("2. Probando diferentes mensajes...")
print()

test_messages = [
    "Prueba de voz en español",
    "¡Atención! Hay una silla muy cerca de ti",
    "¡Cuidado! Hay un auto muy cerca de ti",
    "¡Atención! Hay una persona muy cerca de ti"
]

for i, message in enumerate(test_messages, 1):
    print(f"   Prueba {i}: '{message}'")
    try:
        announcer.engine.say(message)
        announcer.engine.runAndWait()
        print(f"   ✅ Reproducido correctamente")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()

# Probar el método announce_close_object
print("3. Probando announce_close_object...")
print()

test_objects = [
    ("chair", "furniture"),
    ("car", "vehicle"),
    ("person", "person"),
    ("table", "furniture")
]

for obj_name, obj_type in test_objects:
    print(f"   Probando: {obj_name} ({obj_type})")
    try:
        announcer.announce_close_object(obj_name, obj_type)
        print(f"   ✅ Anuncio agregado a la cola")
        # Esperar un momento para que se reproduzca
        import time
        time.sleep(2)
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()

print("=" * 60)
print("PRUEBA COMPLETADA")
print("=" * 60)
print()
print("Si escuchaste las voces, el sistema funciona correctamente.")
print("Si no escuchaste nada, verifica:")
print("  1. El volumen del sistema")
print("  2. Que pyttsx3 esté instalado: pip install pyttsx3")
print("  3. Que el motor de voz esté disponible en tu sistema")





