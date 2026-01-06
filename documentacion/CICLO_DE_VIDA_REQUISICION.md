# 👥 Sistema de Roles para Empleados

## Cambio Implementado

Se agregó un campo `rol` al modelo `Empleado` con 4 valores posibles:

1. **temporal** - Empleado temporal
2. **empleado** - Empleado regular
3. **supervisor** - Supervisor de área
4. **directivo** - Directivo/Gerente

## Modelo Actualizado

```python
class Empleado(models.Model):
    ROL_CHOICES = [
        ('temporal', 'Temporal'),
        ('empleado', 'Empleado'),
        ('supervisor', 'Supervisor'),
        ('directivo', 'Directivo'),
    ]
    
    nombre = models.CharField(max_length=50, unique=True)
    puesto = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='empleado'
    )
    # ... otros campos
    
    def es_supervisor(self):
        """Verifica si es supervisor o directivo"""
        return self.rol in ['supervisor', 'directivo']
    
    def es_directivo(self):
        """Verifica si es directivo"""
        return self.rol == 'directivo'
```

## Métodos de Utilidad

### `empleado.es_supervisor()`
Devuelve `True` si el empleado es **supervisor** o **directivo**.

**Ejemplo:**
```python
if empleado.es_supervisor():
    # Puede aprobar requisiciones
    pass
```

### `empleado.es_directivo()`
Devuelve `True` solo si el empleado es **directivo**.

**Ejemplo:**
```python
if empleado.es_directivo():
    # Puede hacer aprobación final
    pass
```

## Pasos para Aplicar el Cambio

### 1. Ejecutar script de actualización:

```cmd
cd c:\Users\dreat\OneDrive\Escritorio\dead_or_alive\Dreacht_hub_inventario-master\Dreacht_hub_inventario-master
python agregar_rol_empleados.py
```

Este script:
- ✅ Agrega el campo `rol` a la tabla `Almacen_empleado`
- ✅ Establece `'empleado'` como valor por defecto
- ✅ Actualiza todos los empleados existentes
- ✅ Muestra estadísticas de roles

### 2. (Opcional) Crear migración oficial de Django:

```cmd
python manage.py makemigrations Almacen
python manage.py migrate
```

**Nota:** El script directo es más rápido, pero la migración es la forma "oficial" de Django.

## Asignar Roles a Empleados

### Opción 1: Admin de Django

1. Ve a: `http://127.0.0.1:8000/admin/Almacen/empleado/`
2. Selecciona un empleado
3. En el campo **"Rol"**, selecciona:
   - Temporal
   - Empleado
   - Supervisor
   - Directivo
4. Guarda los cambios

### Opción 2: Shell de Django

```cmd
python manage.py shell
```

```python
from Almacen.models.personal.personal import Empleado

# Asignar rol de supervisor
emp = Empleado.objects.get(nombre="Alan Limón")
emp.rol = 'supervisor'
emp.save()

# Asignar rol de directivo
emp = Empleado.objects.get(nombre="Carlos Méndez")
emp.rol = 'directivo'
emp.save()

# Verificar
print(emp.rol)  # 'directivo'
print(emp.es_directivo())  # True
print(emp.es_supervisor())  # True

exit()
```

### Opción 3: Script Python

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
django.setup()

from Almacen.models.personal.personal import Empleado

# Actualizar roles en lote
Empleado.objects.filter(nombre__in=["Alan Limón", "Mariana García"]).update(rol='supervisor')
Empleado.objects.filter(nombre="Carlos Méndez").update(rol='directivo')

print("✓ Roles actualizados")
```

## Uso en el Bot de Telegram

### Ejemplo 1: Verificar permisos para aprobar

```python
from Almacen.models.personal.personal import Empleado

# Obtener empleado asociado al usuario de Telegram
empleado = telegram_user.empleado

if empleado and empleado.es_supervisor():
    # Mostrar botón de aprobar
    await query.edit_message_text(
        "Tienes permisos para aprobar esta requisición",
        reply_markup=Keyboards.aprobar_requisicion()
    )
```

### Ejemplo 2: Filtrar requisiciones por rol

```python
# Ver solo requisiciones que puede aprobar
if empleado.es_directivo():
    # Mostrar requisiciones en estado 'supervisor'
    requisiciones = Requisicion.objects.filter(estado='supervisor')
elif empleado.es_supervisor():
    # Mostrar requisiciones en estado 'pendiente'
    requisiciones = Requisicion.objects.filter(estado='pendiente')
```

### Ejemplo 3: Notificaciones por rol

```python
# Notificar a supervisores de una nueva requisición
supervisores = Empleado.objects.filter(rol='supervisor')
for supervisor in supervisores:
    if supervisor.telegram_user:
        await bot.send_message(
            chat_id=supervisor.telegram_user.telegram_id,
            text=f"Nueva requisición: {requisicion.id}"
        )
```

## Valores por Defecto

| Campo | Valor |
|-------|-------|
| **Empleados nuevos** | `'empleado'` |
| **Empleados existentes** | `'empleado'` (actualizado por script) |

## Flujo de Aprobaciones con Roles

```
┌─────────────────────────────────────────┐
│ Solicitante crea requisición            │
│ Estado: 'pendiente'                     │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Notificar a empleados con rol:          │
│ - 'supervisor'                          │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Supervisor aprueba                      │
│ Estado: 'supervisor'                    │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Notificar a empleados con rol:          │
│ - 'directivo'                           │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Directivo aprueba                       │
│ Estado: 'autorizada'                    │
│ ✅ Descuenta inventario                 │
└─────────────────────────────────────────┘
```

## Validaciones Recomendadas

```python
# En el handler de aprobación de supervisor
if not empleado.es_supervisor():
    await update.message.reply_text(
        "❌ No tienes permisos de supervisor para aprobar esta requisición."
    )
    return

# En el handler de aprobación de directivo
if not empleado.es_directivo():
    await update.message.reply_text(
        "❌ No tienes permisos de directivo para la aprobación final."
    )
    return
```

## Próximos Pasos

1. ✅ Campo `rol` agregado al modelo
2. ⏳ Integrar validaciones en handlers de aprobación
3. ⏳ Implementar notificaciones por rol
4. ⏳ Agregar filtros de requisiciones por permisos

## Verificar Cambios

```cmd
python manage.py shell
```

```python
from Almacen.models.personal.personal import Empleado

# Ver todos los roles disponibles
print(Empleado.ROL_CHOICES)

# Ver empleados y sus roles
for emp in Empleado.objects.all():
    print(f"{emp.nombre}: {emp.get_rol_display()}")

exit()
```
