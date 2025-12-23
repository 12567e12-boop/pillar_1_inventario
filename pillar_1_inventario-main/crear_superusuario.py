"""
Script para crear o verificar superusuario por defecto.
Se ejecuta automáticamente al iniciar el proyecto.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Datos del superusuario
USERNAME = 'Alan'
PASSWORD = 'odal'
EMAIL = 'alan@inventario.com'

try:
    # Verificar si el usuario ya existe
    if User.objects.filter(username=USERNAME).exists():
        user = User.objects.get(username=USERNAME)
        
        # Asegurar que sea superusuario
        if not user.is_superuser or not user.is_staff:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"✓ Usuario '{USERNAME}' actualizado a superusuario")
        else:
            print(f"✓ Superusuario '{USERNAME}' ya existe")
    else:
        # Crear nuevo superusuario
        User.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        print(f"✓ Superusuario '{USERNAME}' creado exitosamente")
    
    print(f"\n  Username: {USERNAME}")
    print(f"  Password: {PASSWORD}")
    print(f"  URL Admin: http://127.0.0.1:8000/admin/")

except Exception as e:
    print(f"✗ Error al crear superusuario: {e}")
