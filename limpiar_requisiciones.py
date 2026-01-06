"""
Script para eliminar todos los registros de requisiciones.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
django.setup()

from Almacen.models.requisiciones import Requisicion, DetalleRequisicion

def limpiar_requisiciones():
    """Elimina todas las requisiciones y sus detalles."""
    
    # Contar registros antes de eliminar
    count_requisiciones = Requisicion.objects.count()
    count_detalles = DetalleRequisicion.objects.count()
    
    print("=" * 60)
    print("  LIMPIEZA DE REQUISICIONES")
    print("=" * 60)
    print(f"\nRegistros encontrados:")
    print(f"  - Requisiciones: {count_requisiciones}")
    print(f"  - Detalles de requisiciones: {count_detalles}")
    
    if count_requisiciones == 0 and count_detalles == 0:
        print("\n✓ No hay registros para eliminar.")
        return
    
    # Confirmar
    respuesta = input("\n¿Deseas eliminar TODOS estos registros? (si/no): ")
    
    if respuesta.lower() in ['si', 's', 'yes', 'y']:
        # Eliminar detalles primero (por integridad referencial)
        DetalleRequisicion.objects.all().delete()
        print(f"✓ Eliminados {count_detalles} detalles de requisiciones")
        
        # Eliminar requisiciones
        Requisicion.objects.all().delete()
        print(f"✓ Eliminadas {count_requisiciones} requisiciones")
        
        print("\n" + "=" * 60)
        print("  LIMPIEZA COMPLETADA")
        print("=" * 60)
    else:
        print("\n✗ Operación cancelada")

if __name__ == '__main__':
    limpiar_requisiciones()
