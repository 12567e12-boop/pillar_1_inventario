"""
Script para verificar y crear bloques si es necesario.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
django.setup()

from Almacen.models.base.base import Bloque

# Verificar bloques existentes
bloques = list(Bloque.objects.all())

print("=" * 60)
print("  BLOQUES REGISTRADOS EN LA BASE DE DATOS")
print("=" * 60)
print(f"\nTotal: {len(bloques)} bloques")

if bloques:
    print("\nLista de bloques:")
    for bloque in bloques:
        print(f"  ID {bloque.id}: {bloque.nombre}")
else:
    print("\n⚠ No hay bloques registrados.")
    print("\n¿Deseas crear bloques de ejemplo? (si/no): ", end="")
    respuesta = input()
    
    if respuesta.lower() in ['si', 's', 'yes', 'y']:
        bloques_ejemplo = [
            "Bloque A",
            "Bloque B", 
            "Bloque C",
            "Zona Norte",
            "Zona Sur"
        ]
        
        for nombre in bloques_ejemplo:
            Bloque.objects.create(nombre=nombre)
            print(f"  ✓ Creado: {nombre}")
        
        print(f"\n✅ Se crearon {len(bloques_ejemplo)} bloques de ejemplo")
    else:
        print("\n✗ Operación cancelada")

print("\n" + "=" * 60)
