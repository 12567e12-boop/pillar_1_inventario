# 🔧 Corrección del Flujo de Requisiciones

## Problema Identificado

El bot estaba creando la requisición **inmediatamente después de seleccionar la especialidad**, sin pedir la imagen. 

### Comportamiento anterior (INCORRECTO):
```
1. Solicitante → ✓
2. Ubicación → ✓
3. Obra → ✓
4. Supervisor → ✓
5. Fecha → ✓
6. Especialidad → ✓ [AQUÍ SE CREABA LA REQUISICIÓN SIN IMAGEN]
```

### Comportamiento corregido (CORRECTO):
```
1. Solicitante → ✓
2. Ubicación → ✓
3. Obra → ✓
4. Supervisor → ✓
5. Fecha → ✓
6. Especialidad → ✓
7. Imagen → ✓ [AHORA SÍ PIDE LA IMAGEN]
8. Crear requisición → ✓
```

## Archivo Modificado

**Archivo:** `Almacen/telegram_bot/requisiciones/handlers_requisiciones.py`

**Función:** `seleccionar_especialidad_callback` (línea ~536)

### Cambio realizado:

**ANTES (Creaba requisición directamente):**
```python
async def seleccionar_especialidad_callback(update, context, especialidad):
    # ... guardar especialidad
    
    # ❌ CREABA REQUISICIÓN INMEDIATAMENTE
    requisicion = await RequisicionService.crear_requisicion(...)
    mensaje = Messages.REQUISICION_CREADA.format(...)
    await query.edit_message_text(mensaje)
```

**DESPUÉS (Pide imagen primero):**
```python
async def seleccionar_especialidad_callback(update, context, especialidad):
    # ... guardar especialidad
    temp_req['especialidad'] = especialidad
    
    # ✓ CAMBIAR ESTADO A ESPERAR IMAGEN
    UserSession.set_user_state(context, 'esperando_imagen')
    
    # ✓ PEDIR LA IMAGEN
    await update.effective_chat.send_message(
        text=Messages.NUEVA_REQUISICION_IMAGEN,
        parse_mode='Markdown',
        reply_markup=Keyboards.esperando_imagen()
    )
```

## Cómo funciona ahora

### Paso 6: Seleccionar Especialidad
Cuando el usuario selecciona una especialidad:
1. Se guarda en `temp_requisicion['especialidad']`
2. Se cambia el estado a `'esperando_imagen'`
3. Se envía mensaje: "📷 Por favor, envía una imagen..."
4. **NO** se crea la requisición todavía

### Paso 7: Enviar Imagen
Cuando el usuario envía una foto:
1. El `photo_handler` detecta el estado `'esperando_imagen'`
2. Descarga y guarda la imagen
3. **AHORA SÍ** llama a `RequisicionService.crear_requisicion()`
4. Crea la requisición con **todos los datos incluyendo la imagen**
5. Muestra mensaje de éxito

## Probar la corrección

1. **Reinicia el bot:**
   ```cmd
   Ctrl+C (para detener)
   iniciar_bot.bat
   ```

2. **En Telegram:**
   ```
   /nueva
   → Juan Pérez [Enter]
   → Zona Norte [Enter]
   → Construcción Edificio A [Enter]
   → [Selecciona supervisor: Alan Limón]
   → 25/12/2024 [Enter]
   → [Selecciona especialidad: Electricidad]
   → [AQUÍ DEBES VER: "📷 Por favor, envía una imagen..."]
   → [Envía una foto desde tu cámara o galería]
   → [VES: "📷 Procesando imagen, por favor espera..."]
   → [VES: "✅ Requisición Creada Exitosamente"]
   ```

## Verificación en logs

Ahora deberías ver en la consola del bot:

```
INFO - Callback recibido: especialidad_Electricidad
INFO - Estado cambiado a: esperando_imagen
INFO - Foto recibida. Estado actual: esperando_imagen
INFO - Procesando imagen para requisición
INFO - Imagen guardada en: media/requisiciones/requisicion_XXXX.jpg
INFO - Requisición creada desde bot: XXX-ZON-0016-ELE
```

## Flujo Completo Corregido

```
┌─────────────────────────────────────────┐
│ Usuario: /nueva                          │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Bot: Ingresa solicitante                │
│ Estado: esperando_solicitante           │
└────────────────┬────────────────────────┘
                 ▼
      ... (pasos intermedios) ...
                 ▼
┌─────────────────────────────────────────┐
│ Usuario: [Selecciona Electricidad]      │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Bot: "✅ Especialidad: Electricidad"    │
│      "📷 Envía una imagen..."           │
│ Estado: esperando_imagen                │
│ temp_req: {todos los datos sin imagen} │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Usuario: [Envía foto 📸]                │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ photo_handler detecta: esperando_imagen │
│   1. Descarga imagen                    │
│   2. Guarda en /media/requisiciones/    │
│   3. temp_req['imagen'] = ruta          │
│   4. crear_requisicion() con imagen     │
│   5. Guarda en BD                       │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Bot: "✅ Requisición creada: XXX-..."   │
│ Estado: limpiado                        │
│ temp_req: limpiado                      │
└─────────────────────────────────────────┘
```

## ¡Listo!

La corrección está completa. Ahora el bot **SÍ PEDIRÁ LA IMAGEN** antes de crear la requisición.
