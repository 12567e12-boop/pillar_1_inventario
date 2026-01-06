# 📦 Dreacht Hub - Sistema de Gestión de Inventario

Un sistema web integral de gestión de inventario con integración de bot de Telegram para solicitud de requisiciones en tiempo real.

## 📋 Tabla de Contenidos
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Funcionamiento General](#-funcionamiento-general)
- [Bot de Requisiciones](#-bot-de-requisiciones)
- [Dependencias Principales](#-dependencias-principales)
- [Agregando un Nuevo Módulo](#-agregando-un-nuevo-módulo)
- [Configuración](#-configuración)
- [Despliegue](#-despliegue)
- [Contribución](#-contribución)

## 🏗️ Estructura del Proyecto

```
Dreacht_hub_inventario/
├── Almacen/                      # Aplicación principal de Django
│   ├── migrations/              # Migraciones de la base de datos
│   ├── models/                  
│   │   ├── personal/           # Modelos de empleados y usuarios
│   │   ├── movimientos/        # Modelos de inventario
│   │   └── requisiciones/      # Modelos de requisiciones
│   ├── services/               # Lógica de negocio
│   ├── templates/              # Plantillas HTML
│   ├── telegram_bot/           # Lógica del bot de Telegram
│   │   ├── handlers/           # Manejadores de comandos
│   │   ├── keyboards/          # Teclados personalizados
│   │   └── services/           # Servicios del bot
│   ├── views/                  # Vistas de la aplicación web
│   ├── admin.py               
│   ├── apps.py
│   └── urls.py
├── Inventario/                 # Configuración de Django
│   ├── settings/              
│   │   ├── base.py           # Configuración base
│   │   ├── development.py    # Configuración de desarrollo
│   │   └── production.py     # Configuración de producción
│   ├── urls.py               # Rutas principales
│   └── wsgi.py               # Configuración WSGI
├── media/                     # Archivos subidos por usuarios
├── static/                    # Archivos estáticos (CSS, JS, imágenes)
├── .env.example              # Variables de entorno de ejemplo
├── manage.py                 
└── requirements/             # Archivos de dependencias
    ├── base.txt             # Dependencias principales
    ├── development.txt      # Dependencias de desarrollo
    └── production.txt       # Dependencias de producción
```

## 🔄 Funcionamiento General

El sistema sigue una arquitectura basada en microservicios con los siguientes componentes principales:

1. **Aplicación Web (Django)**: Interfaz administrativa para gestión completa del inventario.
2. **API REST**: Endpoints para comunicación con el bot y otras integraciones.
3. **Bot de Telegram**: Interfaz para solicitudes de requisiciones por parte de los empleados.
4. **Base de Datos**: Almacena toda la información del sistema.

### Flujo de Datos
1. Los empleados realizan solicitudes a través del bot de Telegram.
2. El bot valida los datos y los envía a la API.
3. La API procesa la solicitud y actualiza la base de datos.
4. Los supervisores revisan y aprueban/rechazan las solicitudes desde el panel web.
5. El sistema actualiza el inventario y notifica a los usuarios.

## 🤖 Bot de Requisiciones

El bot de Telegram permite a los empleados:
- Crear nuevas solicitudes de requisición
- Adjuntar imágenes de los productos
- Recibir notificaciones en tiempo real
- Consultar el estado de sus solicitudes

### Características Técnicas
- **Framework**: python-telegram-bot
- **Patrón**: Usa el patrón de diseño Command para manejar diferentes comandos
- **Persistencia**: Los datos se almacenan en la base de datos principal
- **Seguridad**: Autenticación mediante tokens únicos

## 📦 Dependencias Principales

### Backend (requirements/base.txt)
- Django 5.0.7
- Django REST Framework 3.14.0
- python-telegram-bot 20.7
- Pillow 10.1.0 (procesamiento de imágenes)
- python-dotenv 1.0.0 (manejo de variables de entorno)
- psycopg2-binary 2.9.9 (para PostgreSQL en producción)

### Desarrollo (requirements/development.txt)
- ipdb 0.13.13 (debugging)
- django-debug-toolbar 4.2.0
- coverage 7.3.2 (cobertura de pruebas)

## ➕ Agregando un Nuevo Módulo

Para agregar un nuevo módulo al sistema, sigue estos pasos:

1. **Crear una nueva aplicación Django**
   ```bash
   python manage.py startapp nombre_modulo
   ```

2. **Estructura recomendada**
   ```
   nombre_modulo/
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── models/
   │   ├── __init__.py
   │   └── modelos_especificos.py
   ├── services/
   │   └── logica_negocio.py
   ├── templates/
   │   └── nombre_modulo/
   │       └── vistas.html
   ├── urls.py
   └── views/
       ├── __init__.py
       └── vistas.py
   ```

3. **Registrar la aplicación**
   Agregar al archivo `settings/base.py`:
   ```python
   INSTALLED_APPS += [
       'nombre_modulo.apps.NombreModuloConfig',
   ]
   ```

4. **Crear migraciones**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Integrar con el sistema existente**
   - Agregar URLs al archivo principal de URLs
   - Crear permisos si es necesario
   - Actualizar el menú de navegación

## 🔧 Configuración

### Variables de Entorno
Crea un archivo `.env` basado en `.env.example` con las siguientes variables:

```
DEBUG=True
SECRET_KEY=tu_clave_secreta_aqui
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
```

## 🚀 Despliegue

### Requisitos
- Python 3.8+
- PostgreSQL 13+
- Nginx (recomendado)
- Gunicorn o uWSGI

### Pasos
1. Configurar variables de entorno de producción
2. Instalar dependencias de producción
3. Recolectar archivos estáticos
4. Configurar servidor web (Nginx/Apache)
5. Configurar servicio para el bot de Telegram

## 👥 Contribución

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🎯 Características Principales

### 🏢 Gestión de Inventario
- ✅ Seguimiento de productos en inventario
- ✅ Gestión de empleados por rol (temporal, empleado, supervisor, directivo)
- ✅ Registro de movimientos (entrada/salida)
- ✅ Transferencia de productos entre bloques
- ✅ Alertas de stock bajo
- ✅ Control de préstamos y devoluciones

### 🤖 Bot de Telegram
- ✅ Creación de requisiciones mediante conversación
- ✅ Selección dinámica de supervisores desde BD
- ✅ Validación de fechas (no pasado, máximo 2 semanas futuro)
- ✅ Carga de imágenes y archivos
- ✅ Seguimiento de estado de requisiciones
- ✅ Notificaciones en tiempo real

### 🔐 Seguridad
- ✅ Autenticación de usuarios
- ✅ Control de acceso por rol
- ✅ Validación de datos en tiempo real
- ✅ Protección CSRF
- ✅ Configuración segura de producción

## 🚀 Instalación

### Requisitos Previos
- Python 3.8+
- pip
- Git

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/12567e12-boop/dreacht_inventario_demo.git
cd dreacht_inventario_demo

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual (Windows)
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar settings (IMPORTANTE)
# Copia settings_example.py para obtener un template
# Edita Inventario/settings.py con tus valores

# 6. Ejecutar migraciones
python manage.py migrate

# 7. Crear superusuario (opcional)
python manage.py createsuperuser

# 8. Iniciar servidor
python manage.py runserver
```

## ⚙️ Configuración del Bot de Telegram

1. **Obtener token del bot:**
   - Abre Telegram y busca `@BotFather`
   - Usa `/newbot` para crear un nuevo bot
   - Copia el token generado

2. **Configurar en `settings.py`:**
   ```python
   TELEGRAM_BOT_TOKEN = 'tu_token_aqui'
   ```

3. **Iniciar el bot:**
   ```bash
   python iniciar_bot.bat  # Windows
   # O desde Python
   python manage.py shell
   # Dentro del shell:
   from Almacen.telegram_bot.bot import start_bot
   start_bot()
   ```

## 📊 Estructura del Proyecto

```
Dreacht_hub_inventario/
├── Almacen/                      # Aplicación Django principal
│   ├── models/                   # Modelos de BD
│   │   ├── personal/             # Modelos de empleados
│   │   ├── movimientos/          # Modelos de inventario
│   │   └── requisiciones/        # Modelos de requisiciones
│   ├── views.py                  # Vistas web
│   ├── admin.py                  # Panel de administración
│   └── telegram_bot/             # Bot de Telegram
│       ├── handlers/             # Manejadores de eventos
│       ├── keyboards/            # Teclados y botones
│       ├── services/             # Lógica de negocio
│       └── messages.py           # Plantillas de mensajes
├── Inventario/                   # Configuración de Django
│   ├── settings.py               # Configuración principal
│   ├── urls.py                   # Rutas principales
│   └── wsgi.py                   # WSGI para producción
├── templates/                    # Plantillas HTML
├── static/                       # CSS, JS, imágenes
├── media/                        # Archivos subidos
└── requirements.txt              # Dependencias Python
```

## 🛠️ Tecnologías Utilizadas

- **Backend:** Django 5.0.7
- **Bot:** python-telegram-bot 20.7
- **BD:** SQLite (desarrollo) / PostgreSQL (producción recomendado)
- **Frontend:** Bootstrap + LobiAdmin UI
- **APIs:** Telegram Bot API

## 📝 Uso

### Panel Web
1. Accede a `http://localhost:8000/admin`
2. Inicia sesión con tu superusuario
3. Gestiona productos, empleados, inventario

### Bot de Telegram
1. Busca tu bot en Telegram
2. Usa `/start` para iniciar
3. Sigue los pasos para crear una requisición

## 🔧 Desarrollo

### Estructura de Commits
El proyecto usa commits descriptivos siguiendo este patrón:
- `feat:` Nuevas características
- `fix:` Correcciones de bugs
- `refactor:` Cambios de estructura sin afectar funcionalidad
- `securizar:` Mejoras de seguridad
- `docs:` Cambios en documentación

### Contribuir
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## ⚠️ Notas de Seguridad

Este proyecto está configurado para **desarrollo local**. Antes de desplegar a producción:

1. ✅ Genera una nueva `SECRET_KEY`
2. ✅ Cambia `DEBUG = False`
3. ✅ Configura `ALLOWED_HOSTS` con tu dominio
4. ✅ Usa variables de entorno para datos sensibles
5. ✅ Cambia la base de datos a PostgreSQL
6. ✅ Asegura las credenciales del bot de Telegram

Consulta `settings_example.py` para más detalles.

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles

## 👤 Autor

Desarrollado como sistema de gestión de inventario empresarial.

## 📞 Soporte

Para problemas o preguntas, abre un issue en GitHub.

---

**Demo:** Este repositorio es una versión de demostración sanitizada para portafolio. No contiene datos reales ni credenciales activas.
