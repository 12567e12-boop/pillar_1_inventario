"""
Script para agregar el campo 'rol' a los empleados existentes.
Este script actualiza la base de datos sin necesidad de migraciones.
"""
import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("  AGREGAR CAMPO 'ROL' A EMPLEADOS")
print("=" * 60)
print()

# Conectar a la BD SQLite
db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar si el campo ya existe
cursor.execute("PRAGMA table_info(Almacen_empleado)")
columns = [column[1] for column in cursor.fetchall()]

if 'rol' in columns:
    print("✓ El campo 'rol' ya existe en la tabla Almacen_empleado")
else:
    print("⚙ Agregando campo 'rol' a la tabla Almacen_empleado...")
    try:
        # Agregar la columna con valor por defecto
        cursor.execute("""
            ALTER TABLE Almacen_empleado 
            ADD COLUMN rol VARCHAR(20) DEFAULT 'general' CHECK(rol IN ('general', 'chofer', 'bodeguero'))
        """)
        conn.commit()
        print("✓ Campo 'rol' agregado exitosamente")
        
        # Actualizar empleados existentes
        cursor.execute("UPDATE Almacen_empleado SET rol = 'general' WHERE rol IS NULL")
        conn.commit()
        print(f"✓ Se actualizaron los empleados existentes con rol='general'")
        
    except Exception as e:
        print(f"✗ Error al agregar campo: {e}")
        conn.rollback()

# Mostrar estadísticas
cursor.execute("SELECT COUNT(*) FROM Almacen_empleado")
total = cursor.fetchone()[0]

if 'rol' in columns or cursor.execute("PRAGMA table_info(Almacen_empleado)"):
    cursor.execute("SELECT rol, COUNT(*) FROM Almacen_empleado GROUP BY rol")
    roles = cursor.fetchall()
    
    print()
    print("=" * 60)
    print("  EMPLEADOS POR ROL")
    print("=" * 60)
    print(f"\nTotal empleados: {total}")
    
    if roles:
        print("\nDistribución por rol:")
        for rol, count in roles:
            rol_display = rol if rol else 'Sin rol'
            print(f"  - {rol_display}: {count}")
    else:
        print("\n(No hay empleados registrados)")

conn.close()

print()
print("=" * 60)
print("  PROCESO COMPLETADO")
print("=" * 60)
print()
print("Ahora puedes editar los roles desde el admin de Django:")
print("  http://127.0.0.1:8000/admin/Almacen/empleado/")
print("\nRoles disponibles:")
print("  - empleado (por defecto)")
print("  - chofer")
print("  - bodeguero")
print()
