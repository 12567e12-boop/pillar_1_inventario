"""
Archivo de ejemplo de configuración para settings.py

INSTRUCCIONES:
1. Copia este archivo y cópialo como settings_local.py
2. Genera una SECRET_KEY nueva:
   python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
3. Obtén un token de bot de Telegram de @BotFather
4. Actualiza los valores en settings_local.py
5. En settings.py, importa desde settings_local.py para desarrollo local

EJEMPLO DE USO EN settings.py:
"""

# ===== DEVELOPMENT ONLY =====
# Descomenta esto solo para desarrollo local y cámbialo a tu configuración

# SECRET_KEY - CAMBIAR EN PRODUCCIÓN
# Generar con: python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY_EXAMPLE = 'django-insecure-tu-clave-super-secreta-aqui'

# DEBUG - NUNCA True en producción
DEBUG_EXAMPLE = True

# ALLOWED_HOSTS - Ajustar según tu dominio
ALLOWED_HOSTS_EXAMPLE = ['localhost', '127.0.0.1', 'your-domain.com']

# Token del bot de Telegram
# Obtener de @BotFather en Telegram
TELEGRAM_BOT_TOKEN_EXAMPLE = 'TU_TOKEN_DEL_BOT_AQUI'

# Base de datos (por defecto SQLite está bien para desarrollo)
DATABASES_EXAMPLE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# Para producción, considerar usar PostgreSQL:
# DATABASES_PRODUCTION = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'tu_base_datos',
#         'USER': 'tu_usuario',
#         'PASSWORD': 'tu_contraseña',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
