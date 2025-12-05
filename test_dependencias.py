"""
Script para verificar que todas las dependencias necesarias están instaladas.
"""
import sys

print("=" * 60)
print("  VERIFICACIÓN DE DEPENDENCIAS")
print("=" * 60)
print()

# Lista de módulos a verificar
dependencias = {
    'django': 'Django',
    'telegram': 'python-telegram-bot',
    'PIL': 'Pillow',
    'asgiref': 'asgiref',
}

errores = []

for modulo, nombre in dependencias.items():
    try:
        __import__(modulo)
        print(f"✓ {nombre:30} - INSTALADO")
    except ImportError:
        print(f"✗ {nombre:30} - NO INSTALADO")
        errores.append(nombre)

print()
print("=" * 60)

if errores:
    print("  FALTAN DEPENDENCIAS")
    print("=" * 60)
    print()
    print("Ejecuta este comando para instalar:")
    print()
    print("  pip install " + " ".join(errores))
    print()
else:
    print("  TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS")
    print("=" * 60)
    print()
    print("✓ El bot está listo para funcionar")
    print()

# Verificar configuración de Django
try:
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
    django.setup()
    
    from django.conf import settings
    
    print("Configuración de Django:")
    print(f"  - BASE_DIR: {settings.BASE_DIR}")
    print(f"  - MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"  - TELEGRAM_BOT_TOKEN: {'Configurado' if hasattr(settings, 'TELEGRAM_BOT_TOKEN') else 'NO CONFIGURADO'}")
    
    # Verificar que el directorio media existe
    import pathlib
    media_path = pathlib.Path(settings.MEDIA_ROOT) / 'requisiciones'
    media_path.mkdir(parents=True, exist_ok=True)
    print(f"  - Directorio media/requisiciones: ✓ Creado")
    
except Exception as e:
    print(f"\n⚠ Advertencia al verificar Django: {e}")

print()
