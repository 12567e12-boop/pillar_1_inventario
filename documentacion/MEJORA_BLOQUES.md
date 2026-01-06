# 🔧 Mejora: Selección de Bloques con Botones

## Cambio Implementado

En el **Paso 2** (Ubicación), el usuario ahora **selecciona el bloque mediante botones** en lugar de escribir texto libre.

## Antes vs Después

### ❌ ANTES (Texto libre):
```
Usuario: /nueva
Bot: Paso 1: Ingresa el nombre del solicitante
Usuario: Juan Pérez
Bot: Paso 2: Ingresa la ubicación
Usuario: [escribe texto libre] → Zona Norte
Bot: Paso 3: Ingresa el nombre de la obra
...
```

### ✅ AHORA (Botones):
```
Usuario: /nueva
Bot: Paso 1: Ingresa el nombre del solicitante
Usuario: Juan Pérez
Bot: Paso 2: Selecciona el bloque/ubicación:
     [🏢 Bloque A] [🏢 Bloque B] [🏢 Bloque C]
Usuario: [Clic en botón "Bloque A"]
Bot: ✅ Bloque/Ubicación seleccionado: Bloque A
     Paso 3: Ingresa el nombre de la obra
...
```

## Archivos Modificados

### 1. `services_requisiciones.py`
**Agregado:**
```python
@staticmethod
@sync_to_async
def obtener_bloques() -> List[Bloque]:
    """Obtiene todos los bloques disponibles"""
    return list(Bloque.objects.all().order_by('nombre'))
```

### 2. `handlers_requisiciones.py`

**Modificado `handle_esperando_solicitante`:**
- Cambia estado a `'esperando_bloque'` (antes era `'esperando_ubicacion'`)
- Obtiene bloques de la BD: `bloques = await CatalogoService.obtener_bloques()`
- Muestra teclado con bloques: `Keyboards.seleccionar_bloque(bloques)`

**Agregado `seleccionar_bloque_callback`:**
```python
async def seleccionar_bloque_callback(update, context, bloque_id):
    # Obtiene el bloque de la BD
    bloque = await sync_to_async(Bloque.objects.get)(id=bloque_id)
    
    # Guarda en sesión
    temp_req['bloque_id'] = bloque_id
    temp_req['ubicacion'] = bloque.nombre
    
    # Cambia a siguiente paso
    UserSession.set_user_state(context, 'esperando_obra')
```

**Agregado en `handle_requisicion_callbacks`:**
```python
if data.startswith("bloque_"):
    bloque_id = int(data.replace("bloque_", ""))
    await seleccionar_bloque_callback(update, context, bloque_id)
    return True
```

**Eliminado:**
- Estado `'esperando_ubicacion'` del handler de mensajes
- Función `handle_esperando_ubicacion()` (ya no se usa)

### 3. `keyboards.py`
Ya existía el teclado `seleccionar_bloque(bloques)` que se reutilizó.

## Flujo Actualizado

```
┌─────────────────────────────────────────┐
│ /nueva                                   │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Paso 1: Nombre del solicitante          │
│ Estado: esperando_solicitante           │
│ Input: Texto libre                       │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Paso 2: Seleccionar bloque/ubicación    │
│ Estado: esperando_bloque                │
│ ✨ CARGA BLOQUES DE LA BD               │
│ Input: Botones inline                   │
│   [Bloque A] [Bloque B] [Bloque C]      │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Guarda: bloque_id + ubicacion (nombre)  │
│ temp_req = {                            │
│   'solicitante_nombre': 'Juan Pérez',   │
│   'bloque_id': 1,                       │
│   'ubicacion': 'Bloque A'               │
│ }                                       │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Paso 3: Nombre de la obra               │
│ Estado: esperando_obra                  │
│ Input: Texto libre                       │
└─────────────────────────────────────────┘
```

## Datos Guardados en Requisición

Ahora se guardan **dos campos relacionados con el bloque**:

```python
Requisicion:
  - bloque_id: 1 (ID del bloque en BD)
  - ubicacion: "Bloque A" (nombre del bloque)
```

Esto permite:
1. **Relación con el modelo Bloque** para futuras consultas
2. **Mostrar el nombre legible** en mensajes y reportes

## Beneficios

✅ **Consistencia:** Solo se pueden seleccionar bloques existentes en la BD
✅ **Sin errores:** No hay typos ni variaciones de texto
✅ **Mejor UX:** Más rápido hacer clic que escribir
✅ **Escalable:** Si se agregan bloques, aparecen automáticamente
✅ **Validación:** No se acepta entrada inválida

## Cómo Probar

1. **Reinicia el bot:**
   ```cmd
   limpiar_cache.bat
   iniciar_bot.bat
   ```

2. **En Telegram:**
   ```
   /nueva
   → Juan Pérez [Enter]
   → [DEBES VER BOTONES CON LOS BLOQUES] 📍
   → [Clic en un bloque]
   → [Continúa con la obra...]
   ```

3. **Si no hay bloques:**
   - Mensaje: "❌ No hay bloques registrados..."
   - Se cancela la creación
   - Necesitas crear bloques en el admin de Django

## Agregar Bloques (si no hay)

Opción 1 - **Admin de Django:**
```
http://127.0.0.1:8000/admin/
→ Bloques
→ Agregar Bloque
```

Opción 2 - **Shell de Django:**
```cmd
python manage.py shell
```
```python
from Almacen.models.base.base import Bloque
Bloque.objects.create(nombre="Bloque A")
Bloque.objects.create(nombre="Bloque B")
Bloque.objects.create(nombre="Bloque C")
print("✓ Bloques creados")
exit()
```

## ¡Listo!

La selección de bloques ahora funciona con botones dinámicos cargados desde la base de datos.
