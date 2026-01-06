# 🏗️ Arquitectura del Sistema - Dreacht Hub Inventario

## Índice
1. [Visión General](#visión-general)
2. [Capas de la Aplicación](#capas-de-la-aplicación)
3. [Modelos de Datos](#modelos-de-datos)
4. [Bot de Telegram](#bot-de-telegram)
5. [Flujos de Proceso](#flujos-de-proceso)
6. [Patrones de Diseño](#patrones-de-diseño)
7. [Seguridad](#seguridad)
8. [Desplegamiento](#desplegamiento)

---

## Visión General

El sistema está dividido en **3 componentes principales**:

```
┌─────────────────────────────────────────────────────────┐
│           USUARIO FINAL (Web + Telegram)                │
└──────────────┬──────────────────────────────────────────┘
               │
     ┌─────────┴──────────────┐
     │                        │
┌────▼──────────┐    ┌───────▼──────────┐
│  Interface    │    │  Telegram Bot    │
│  Web (Django) │    │  (Bot API)       │
└────┬──────────┘    └───────┬──────────┘
     │                       │
     └───────────┬───────────┘
                 │
         ┌───────▼───────────┐
         │  Capa de Lógica   │
         │   (Services)      │
         └───────┬───────────┘
                 │
         ┌───────▼───────────┐
         │  Capa de Datos    │
         │  (Models + BD)    │
         └───────────────────┘
```

---

## Capas de la Aplicación

### 1️⃣ Capa de Presentación

#### 1.1 Web (Django Templates)
- **Ubicación:** `Almacen/templates/`
- **Tecnología:** Django Templates + Bootstrap + LobiAdmin
- **Responsabilidad:** Interfaz web para gestión de inventario
- **Vistas principales:**
  - Dashboard de inventario
  - Gestión de productos
  - Gestión de empleados
  - Reporte de requisiciones

**Estructura de Templates:**
```
templates/
├── base.html                 # Template base (navbar, sidebar)
├── dashboard.html            # Dashboard principal
├── inventario/
│   ├── productos.html       # Listado de productos
│   ├── producto_form.html   # Crear/editar producto
│   └── movimientos.html     # Historial de movimientos
├── empleados/
│   ├── listado.html         # Listado de empleados
│   └── empleado_form.html   # Crear/editar empleado
└── requisiciones/
    ├── listado.html         # Listado de requisiciones
    └── detalle.html         # Detalles de requisición
```

#### 1.2 Bot de Telegram
- **Ubicación:** `Almacen/telegram_bot/`
- **Tecnología:** python-telegram-bot 20.7
- **Responsabilidad:** Interface conversacional para requisiciones
- **Características:**
  - Creación de requisiciones mediante chat
  - Selección dinámica de opciones desde BD
  - Validación de datos en tiempo real
  - Manejo de estados de conversación

**Estructura del Bot:**
```
telegram_bot/
├── bot.py                   # Inicializador del bot
├── handlers/                # Manejadores de eventos
│   ├── handlers_requisiciones.py   # Flujo de requisiciones
│   ├── handlers_empleados.py       # Gestión de empleados
│   └── handlers_utils.py           # Utilidades
├── keyboards/               # Botones y menús
│   ├── keyboards.py         # Generador de teclados
│   └── callbacks.py         # Manejo de callbacks
├── services/                # Lógica de negocio
│   ├── services_requisiciones.py   # CRUD y queries
│   ├── services_inventario.py      # Movimientos
│   └── services_empleados.py       # Gestión de empleados
├── messages.py              # Plantillas de mensajes
└── requisiciones/           # Módulo específico de requisiciones
    ├── handlers_requisiciones.py
    ├── keyboards.py
    └── services_requisiciones.py
```

---

### 2️⃣ Capa de Lógica de Negocio

#### 2.1 Services (Servicios)
- **Ubicación:** `Almacen/telegram_bot/requisiciones/services_requisiciones.py`
- **Patrón:** Separación de lógica de negocio de handlers
- **Principio:** Single Responsibility (una clase = una responsabilidad)

**Clases principales:**
```python
# RequisicionService
- crear_requisicion(datos) → Requisicion
- obtener_requisicion(id) → Requisicion
- listar_requisiciones() → List[Requisicion]
- cambiar_estado(id, nuevo_estado) → bool

# CatalogoService
- listar_productos() → List[Producto]
- listar_empleados() → List[Empleado]
- listar_supervisores() → List[Empleado]
- listar_unidades() → List[Unidad]
- buscar_producto(nombre) → List[Producto]
```

#### 2.2 Async/Await Pattern
- **Motivo:** python-telegram-bot es completamente asincrónico
- **Decorador:** `@sync_to_async` para operaciones de BD
- **Beneficio:** No bloquea el event loop de Telegram

**Ejemplo:**
```python
@sync_to_async
def listar_productos():
    """Obtiene productos de forma thread-safe"""
    return list(Producto.objects.all())

# Uso en handler
productos = await CatalogoService.listar_productos()
```

---

### 3️⃣ Capa de Datos (Modelos)

#### 3.1 Estructura de Modelos
```
models/
├── __init__.py
├── base/
│   └── modelos_base.py       # AbstractModel con timestamps
├── personal/
│   ├── empleado.py           # Modelo Empleado (rol: temporal/empleado/supervisor/directivo)
│   └── gafete.py            # Modelo GafeteEmpleado (PDF de identificación)
├── movimientos/
│   ├── inventario.py         # Stock actual de productos
│   ├── registro.py           # Historial de movimientos (entrada/salida)
│   ├── transferencia.py      # Transferencias entre bloques
│   └── prestamo.py           # Préstamos y devoluciones
├── requisiciones/
│   ├── requisicion.py        # Requisiciones (estado: pendiente→supervisor→autorizada→surtida→cerrada)
│   ├── detalle_requisicion.py # Líneas de requisición
│   └── telegram_user.py      # Mapeo usuario Telegram → Empleado
└── catalogo/
    ├── bloque.py             # Ubicación física (almacén, sector)
    ├── producto.py           # Catálogo de productos
    └── unidad.py             # Unidades de medida
```

#### 3.2 Diagrama ER Simplificado

```
┌─────────────────┐
│   Empleado      │
├─────────────────┤
│ id (PK)         │
│ nombre          │
│ rol             │ ◄─────── (temporal/empleado/supervisor/directivo)
│ puesto          │
│ telefono        │
│ nss             │
│ direccion       │
│ foto            │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐         ┌─────────────────┐
│  Requisicion    │◄────────┤  TelegramUser   │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ user_id         │
│ token_publico   │         │ empleado_id (FK)│
│ solicitante     │         │ chat_id         │
│ fecha_creacion  │         └─────────────────┘
│ fecha_util      │
│ estado          │
│ supervisor_id   │
│ especialidad    │
│ imagen          │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼──────────────────┐
│  DetalleRequisicion       │
├──────────────────────────┤
│ id (PK)                  │
│ requisicion_id (FK)      │
│ producto_id (FK)         │
│ cantidad_solicitada      │
│ cantidad_confirmada      │
│ unidad_id (FK)           │
└──────────────────────────┘
```

#### 3.3 Estados de Requisición

```
┌──────────┐
│ Pendiente│  ← Creada desde Telegram
└────┬─────┘
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← Esperando aprobación de supervisor
└────┬─────────┘
     │
     ├─────────────┬──────────────┐
     │             │              │
     ▼ Aprobada    ▼ Rechazada    │
┌──────────┐   ┌──────────┐       │
│Autorizada│   │Rechazada │       │
└────┬─────┘   └──────────┘       │
     │                            │
     ▼                            │
┌──────────┐                      │
│  Surtida │  ← Stock confirmado  │
└────┬─────┘                      │
     │                            │
     ▼                            │
┌──────────┐                      │
│  Cerrada │ ◄─────────────────────┘
└──────────┘
```

---

## Bot de Telegram

### Flujo de Creación de Requisición (Step-by-step)

```
┌─────────────────────────────────────────────────────────────┐
│                    START (/start, /nuevareq)                │
└────────────────┬────────────────────────────────────────────┘
                 │
        Paso 1: Seleccionar Bloque
                 │
     ┌───────────▼───────────┐
     │ ¿En qué bloque?       │
     │ [Almacén] [Sector A]  │
     └───────────┬───────────┘
                 │
        Paso 2: Seleccionar Producto
                 │
     ┌───────────▼──────────────────┐
     │ ¿Qué producto?               │
     │ [Buscar] o [Listar todos]    │
     └───────────┬──────────────────┘
                 │
        Paso 3: Cantidad
                 │
     ┌───────────▼──────────────────┐
     │ ¿Cuánta cantidad?            │
     │ [Usuario ingresa número]     │
     └───────────┬──────────────────┘
                 │
        Paso 4: Seleccionar Supervisor
                 │
     ┌───────────▼──────────────────────────┐
     │ ¿Quién aprueba?                      │
     │ [Cargar dinámicamente de BD]          │
     │ [Filtro: rol='supervisor']           │
     └───────────┬──────────────────────────┘
                 │
        Paso 5: Fecha Útil
                 │
     ┌───────────▼────────────────────────────┐
     │ ¿Fecha a utilizar? (DD/MM/YYYY)       │
     │ Validar: >= hoy, <= hoy + 14 días    │
     └───────────┬────────────────────────────┘
                 │
        Paso 6: Especialidad
                 │
     ┌───────────▼──────────────────┐
     │ ¿Especialidad?               │
     │ [Mantenimiento] [Limpieza]   │
     └───────────┬──────────────────┘
                 │
        Paso 7: Imagen
                 │
     ┌───────────▼──────────────────┐
     │ Adjunta una imagen (opcional)│
     │ o escribe /skip para omitir  │
     └───────────┬──────────────────┘
                 │
        Paso 8: Confirmación
                 │
     ┌───────────▼────────────────────┐
     │ ✅ Requisición creada!         │
     │ Token: {uuid}                  │
     │ Estado: Pendiente              │
     │ Supervisor asignado: {nombre}  │
     └────────────────────────────────┘
```

### Diagrama de Estados (State Machine)

```python
# UserSession state tracking
ESTADOS_USUARIO = {
    'esperando_bloque': 1,
    'esperando_producto': 2,
    'esperando_cantidad': 3,
    'esperando_supervisor': 4,
    'esperando_fecha_util': 5,
    'esperando_especialidad': 6,
    'esperando_imagen': 7,
    'confirmacion': 8,
}

# Transiciones válidas
{
    1: 2,  # bloque → producto
    2: 3,  # producto → cantidad
    3: 4,  # cantidad → supervisor
    4: 5,  # supervisor → fecha
    5: 6,  # fecha → especialidad
    6: 7,  # especialidad → imagen
    7: 8,  # imagen → confirmación
}
```

---

## Flujos de Proceso

### 1. Flujo Web: Gestión de Inventario

```
Usuario (Admin)
    │
    ▼
Login Django
    │
    ▼
┌─────────────────────────────┐
│ Seleccionar Operación:      │
│ - Ver Productos             │
│ - Agregar Producto          │
│ - Ver Movimientos           │
│ - Autorizar Requisición     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Realizar Acción             │
│ (GET/POST a Django View)    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Procesar en Service         │
│ (Validar, calcular, guardar)│
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Guardar en BD               │
│ (Django ORM → SQLite/PG)    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Retornar Resultado          │
│ (HTML renderizado)          │
└─────────────────────────────┘
```

### 2. Flujo Bot: Requisición en Telegram

```
Usuario Telegram
    │
    ▼
/start o /nuevareq
    │
    ▼
┌─────────────────────────────────┐
│ Handler: handle_start()         │
│ - Verificar si es usuario nuevo │
│ - Crear o actualizar TelegramUser│
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Mostrar Menú Principal          │
│ - Nueva Requisición             │
│ - Ver mis Requisiciones         │
│ - Ayuda                         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Flujo Multi-paso                │
│ (8 pasos - ver diagrama arriba) │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Crear Requisicion               │
│ - Service.crear_requisicion()   │
│ - Generar token_publico (UUID)  │
│ - Estado = 'pendiente'          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Enviar a Supervisor             │
│ - Notificación privada al       │
│   supervisor asignado           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ ✅ Confirmación al Usuario      │
│ "Tu requisición fue creada"     │
└─────────────────────────────────┘
```

---

## Patrones de Diseño

### 1. Service Layer Pattern
**Ubicación:** `services_requisiciones.py`
**Beneficio:** Lógica centralizada, testeable, reutilizable

```python
class RequisicionService:
    """Aislamiento de lógica de negocio"""
    
    @staticmethod
    @sync_to_async
    def crear_requisicion(datos: dict) -> Requisicion:
        """Crear requisición con validación"""
        # Validar datos
        # Guardar en BD
        # Retornar objeto
        pass
```

### 2. Message Template Pattern
**Ubicación:** `messages.py`
**Beneficio:** Centralización de texto, fácil mantenimiento multiidioma

```python
class Messages:
    """Plantillas de mensajes centralizadas"""
    
    BIENVENIDA = "🤖 Bienvenido a {empresa}..."
    NUEVA_REQUISICION = "📝 Crear nueva requisición..."
    
    @staticmethod
    def obtener_mensaje_fecha_util():
        """Genera mensaje dinámico con fecha actual"""
        fecha_hoy = date.today().strftime("%d/%m/%Y")
        return Messages.NUEVA_REQUISICION_FECHA_UTIL.format(
            fecha_actual=fecha_hoy
        )
```

### 3. Keyboard Factory Pattern
**Ubicación:** `keyboards.py`
**Beneficio:** Generación dinámica de UI buttons desde BD

```python
class Keyboards:
    """Factory para teclados dinámicos"""
    
    @staticmethod
    def seleccionar_supervisor(supervisores: List[Empleado]):
        """Crea botones dinámicamente"""
        keyboard = []
        for supervisor in supervisores:
            keyboard.append([
                InlineKeyboardButton(
                    text=supervisor.nombre,
                    callback_data=f"supervisor_{supervisor.id}"
                )
            ])
        return InlineKeyboardMarkup(keyboard)
```

### 4. State Machine Pattern
**Ubicación:** `handlers_requisiciones.py`
**Beneficio:** Manejo limpio de flujos multi-paso

```python
UserSession.set_user_state(context, 'esperando_producto')
# → Siguiente handler solo procesa si estado = 'esperando_producto'
```

### 5. Decorator Pattern (@sync_to_async)
**Beneficio:** Thread-safety para operaciones de BD en async code

```python
@sync_to_async
def listar_productos():
    """Ejecuta en thread pool, no bloquea event loop"""
    return list(Producto.objects.all())
```

---

## Seguridad

### 1. Autenticación y Autorización

**Web:**
- ✅ Django auth + Login required
- ✅ Roles: admin, usuario, supervisor, directivo
- ✅ Permissions a nivel de vista

**Bot:**
- ✅ Mapeo TelegramUser → Empleado
- ✅ Validación de `chat_id` en handlers
- ✅ Roles determinan qué operaciones pueden hacer

### 2. Validación de Datos

```python
# Ejemplo: Validación de fecha en Paso 5
def handle_esperando_fecha_util(update, context, text):
    try:
        fecha_ingresada = datetime.strptime(text, '%d/%m/%Y').date()
    except ValueError:
        # Rechazar formato inválido
        return
    
    # Validar rango
    hoy = date.today()
    if fecha_ingresada < hoy:
        # Error: anterior a hoy
        return
    
    if fecha_ingresada > hoy + timedelta(days=14):
        # Error: muy lejana
        return
    
    # ✅ Válida
    guardar_fecha(fecha_ingresada)
```

### 3. CSRF Protection
- ✅ Django CSRF Middleware activo
- ✅ Tokens en formularios POST
- ✅ CSRF_TRUSTED_ORIGINS configurado para ngrok

### 4. SQL Injection Protection
- ✅ Django ORM (parametrizado automáticamente)
- ✅ No hay raw SQL en el código

### 5. XSS Protection
- ✅ Django Template autoescape por defecto
- ✅ Markdown escaping en mensajes del bot

---

## Desplegamiento

### Ambiente Local (Desarrollo)

```bash
# 1. Clonar repo
git clone https://github.com/12567e12-boop/dreacht_inventario_demo.git
cd dreacht_inventario_demo

# 2. Ambiente virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Base de datos
python manage.py migrate

# 5. Ejecutar servidor
python manage.py runserver  # Web: http://localhost:8000
python iniciar_bot.bat      # Bot: polling
```

### Ambiente de Producción (Recomendado)

```
┌──────────────────┐
│  Nginx/Apache    │  ← Proxy inverso + SSL/TLS
└────────┬─────────┘
         │
┌────────▼──────────┐
│  Gunicorn/uWSGI   │  ← Servidor WSGI multithread
└────────┬──────────┘
         │
┌────────▼──────────┐
│  Django App       │  ← DEBUG=False, SECRET_KEY en env
│  + Bot (async)    │
└────────┬──────────┘
         │
┌────────▼──────────┐
│  PostgreSQL       │  ← BD de producción
│  (no SQLite)      │
└───────────────────┘
```

**Checklist Pre-Producción:**
- [ ] Generar nueva `SECRET_KEY`
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS = ['tu-dominio.com']`
- [ ] Base de datos PostgreSQL
- [ ] Variables de entorno (.env)
- [ ] SSL/TLS en Nginx
- [ ] Backups automáticos de BD
- [ ] Logs centralizados (syslog/ELK)
- [ ] Monitoreo (uptime, errores)
- [ ] Rate limiting en API

---

## Integración Continua (CI/CD)

**Sugerido:**
- GitHub Actions para tests
- Deploy automático a servidor
- Backup pre-deploy de BD

```yaml
# .github/workflows/deploy.yml (sugerido)
name: Deploy to Production
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python manage.py test
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        run: ./scripts/deploy.sh
```

---

## Extensiones Futuras

### 1. Notificaciones por Email
```python
# Send email cuando requisición es aprobada
from django.core.mail import send_mail
send_mail('Requisición Aprobada', ...)
```

### 2. Reportes Avanzados
```python
# Reportes de consumo por empleado/bloque
from django.db.models import Sum, Count
Registro.objects.values('bloque').annotate(total=Sum('cantidad'))
```

### 3. Integración con Sistema ERP
```python
# Exportar requisiciones a SAP/Oracle
# Importar catálogo de productos desde ERP
```

### 4. Mobile App (React Native)
```
Compartir mismo backend (Django API)
Adicionar Django REST Framework
```

---

## Documentación Relacionada

- [README.md](README.md) - Guía de instalación
- [settings_example.py](settings_example.py) - Configuración
- [ROLES_EMPLEADOS.md](ROLES_EMPLEADOS.md) - Sistema de roles
- Código fuente con docstrings

---

**Última actualización:** 2025-11-14
**Versión:** 1.0 - Demostración para Portafolio
