# Bot de Telegram - Sistema de Requisiciones

Bot de Telegram integrado con Django para gestionar el ciclo de vida completo de requisiciones de materiales.

## 📋 Características

- ✅ Crear nuevas requisiciones
- 📋 Listar requisiciones del usuario
- 👁️ Ver detalles de requisiciones
- ✅ Aprobar requisiciones (Supervisor y Directivo)
- ❌ Rechazar requisiciones
- 📦 Marcar como surtida
- 🔒 Cerrar requisiciones
- 🔔 Notificaciones en tiempo real

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install python-telegram-bot
```

### 2. Configurar el token del bot

Agrega en `Inventario/settings.py`:

```python
# Token del bot de Telegram
TELEGRAM_BOT_TOKEN = 'tu_token_aqui'
```

Para obtener un token:
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Usa el comando `/newbot`
3. Sigue las instrucciones
4. Copia el token que te proporciona

### 3. Ejecutar el bot

```bash
python manage.py run_telegram_bot
```

O con token por argumento:

```bash
python manage.py run_telegram_bot --token "tu_token_aqui"
```

## 📱 Comandos Disponibles

### Comandos Básicos
- `/start` - Iniciar el bot y ver menú principal
- `/help` - Ver ayuda y comandos disponibles

### Comandos de Usuario
- `/nueva` - Crear una nueva requisición
- `/mis_requisiciones` - Ver todas tus requisiciones
- `/ver <ID>` - Ver detalles de una requisición específica

### Comandos de Supervisor/Directivo
- `/aprobar <ID>` - Aprobar una requisición
- `/rechazar <ID>` - Rechazar una requisición

## 🔄 Flujo de Trabajo

### 1. Crear Requisición
```
Usuario → /nueva
Bot → Solicita: Obra
Usuario → Ingresa nombre de obra
Bot → Solicita: Ubicación
Usuario → Ingresa ubicación
Bot → Solicita: Especialidad
Usuario → Ingresa especialidad
Bot → ✅ Requisición creada (Estado: Pendiente)
```

### 2. Aprobación por Supervisor
```
Supervisor → /aprobar REQ-001
Bot → Solicita confirmación
Supervisor → Confirma
Bot → ✅ Aprobada por supervisor (Estado: Supervisor)
```

### 3. Aprobación por Directivo
```
Directivo → /aprobar REQ-001
Bot → Solicita confirmación
Directivo → Confirma
Bot → ✅ Aprobada por directivo (Estado: Autorizada)
Bot → 📦 Inventario descontado automáticamente
```

### 4. Surtir Requisición
```
Almacenista → Selecciona requisición
Almacenista → Marca como surtida
Bot → ✅ Requisición surtida (Estado: Surtida)
```

### 5. Cerrar Requisición
```
Supervisor → Selecciona requisición
Supervisor → Cierra requisición
Bot → ✅ Requisición cerrada (Estado: Cerrada)
```

## 🎨 Estados de Requisiciones

| Estado | Emoji | Descripción |
|--------|-------|-------------|
| Pendiente | 🟡 | Esperando aprobación del supervisor |
| Supervisor | 🟠 | Aprobada por supervisor, esperando directivo |
| Autorizada | 🟢 | Aprobada completamente, lista para surtir |
| Surtida | 🔵 | Materiales entregados |
| Cerrada | ⚫ | Requisición finalizada |
| Rechazada | 🔴 | Requisición rechazada |

## 🔐 Permisos

### Usuario Regular
- Crear requisiciones
- Ver sus propias requisiciones
- Ver detalles de requisiciones

### Supervisor
- Todos los permisos de usuario
- Aprobar requisiciones (primera aprobación)
- Rechazar requisiciones
- Cerrar requisiciones

### Directivo
- Todos los permisos de supervisor
- Aprobar requisiciones (segunda aprobación)
- Autorizar descuento de inventario

## 🏗️ Arquitectura

```
Almacen/
├── telegram_bot/
│   ├── __init__.py          # Inicialización del módulo
│   ├── bot.py               # Configuración principal del bot
│   ├── handlers.py          # Manejadores de comandos y callbacks
│   ├── keyboards.py         # Teclados inline
│   ├── messages.py          # Templates de mensajes
│   ├── services.py          # Lógica de negocio
│   ├── utils.py             # Utilidades y decoradores
│   └── README.md            # Esta documentación
├── management/
│   └── commands/
│       └── run_telegram_bot.py  # Comando Django
└── models/
    └── requisiciones/       # Modelos de requisiciones
```

## 🔧 Configuración Avanzada

### Vincular usuarios de Telegram con Django

En `utils.py`, implementa la lógica de autenticación:

```python
def get_django_user_from_telegram(telegram_id):
    """
    Vincula un usuario de Telegram con un usuario de Django.
    """
    # Implementa tu lógica aquí
    # Por ejemplo, usando un modelo TelegramUser
    pass
```

### Personalizar permisos

En `utils.py`, modifica los decoradores:

```python
@require_supervisor
def handler(update, context):
    # Implementa verificación real de permisos
    user = get_django_user_from_telegram(update.effective_user.id)
    if not user.groups.filter(name='Supervisores').exists():
        return False
    return True
```

## 📊 Integración con Modelos

El bot interactúa directamente con los modelos de Django:

```python
from Almacen.models.requisiciones.requisiciones import Requisicion
from Almacen.models.requisiciones.detalles import DetalleRequisicion
from Almacen.models.base.base import Bloque, Empleado, Producto
```

## 🐛 Debugging

Para ver logs detallados:

```python
# En bot.py, ajusta el nivel de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Cambiar a DEBUG
)
```

## 🔄 Actualización

Para actualizar el bot después de cambios en el código:

1. Detén el bot (Ctrl+C)
2. Realiza los cambios necesarios
3. Reinicia el bot: `python manage.py run_telegram_bot`

## 📝 Notas Importantes

- El bot usa **polling** (no webhooks) para simplicidad
- Las sesiones de usuario se mantienen en memoria (se pierden al reiniciar)
- Para producción, considera usar webhooks y Redis para sesiones
- Implementa autenticación real antes de usar en producción

## 🤝 Contribuir

Para agregar nuevas funcionalidades:

1. Agrega el comando en `handlers.py`
2. Crea el mensaje en `messages.py`
3. Crea el teclado en `keyboards.py` (si es necesario)
4. Agrega la lógica de negocio en `services.py`
5. Registra el handler en `bot.py`

## 📞 Soporte

Para problemas o preguntas, contacta al administrador del sistema.

## 📄 Licencia

Este módulo es parte del Sistema de Inventario y sigue la misma licencia del proyecto principal.
