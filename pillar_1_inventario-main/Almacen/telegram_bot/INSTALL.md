# 🚀 Guía de Instalación Rápida - Bot de Telegram

## Paso 1: Instalar Dependencias

Activa tu entorno virtual y ejecuta:

```bash
# Activar entorno virtual (si usas laZona)
laZona\Scripts\activate

# Instalar python-telegram-bot
pip install python-telegram-bot==20.7
```

## Paso 2: Crear el Bot en Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía el comando `/newbot`
3. Sigue las instrucciones:
   - Nombre del bot: `Sistema de Requisiciones` (o el que prefieras)
   - Username del bot: `tu_empresa_requisiciones_bot` (debe terminar en `_bot`)
4. **Copia el token** que te proporciona (algo como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Paso 3: Configurar el Token

Abre `Inventario/settings.py` y agrega tu token:

```python
# Token del bot de Telegram
TELEGRAM_BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'  # Tu token aquí
```

## Paso 4: Ejecutar el Bot

```bash
python manage.py run_telegram_bot
```

Deberías ver:

```
============================================================
  Bot de Telegram - Sistema de Requisiciones
============================================================
El bot está activo y esperando mensajes...
Presiona Ctrl+C para detener el bot.
============================================================
```

## Paso 5: Probar el Bot

1. Busca tu bot en Telegram por el username que elegiste
2. Envía `/start`
3. Deberías recibir el mensaje de bienvenida

## 🎉 ¡Listo!

Tu bot está funcionando. Ahora puedes:

- Crear requisiciones con `/nueva`
- Ver tus requisiciones con `/mis_requisiciones`
- Aprobar requisiciones con `/aprobar <ID>`

## 🔧 Solución de Problemas

### Error: "TELEGRAM_BOT_TOKEN no está configurado"

**Solución:** Verifica que agregaste el token en `settings.py`

### Error: "Couldn't import Django"

**Solución:** Asegúrate de estar en el entorno virtual:
```bash
laZona\Scripts\activate
```

### El bot no responde

**Solución:** 
1. Verifica que el bot esté ejecutándose
2. Revisa que el token sea correcto
3. Verifica la conexión a internet

### Error al importar módulos

**Solución:** Instala las dependencias:
```bash
pip install python-telegram-bot==20.7
```

## 📝 Notas Importantes

- El bot debe estar **siempre ejecutándose** para recibir mensajes
- Para producción, considera usar **systemd** o **supervisor** para mantener el bot activo
- Los logs se muestran en la consola donde ejecutaste el comando

## 🔄 Actualizar el Bot

Si haces cambios en el código:

1. Detén el bot (Ctrl+C)
2. Guarda los cambios
3. Reinicia el bot: `python manage.py run_telegram_bot`

## 📚 Más Información

Lee el archivo `README.md` para documentación completa sobre:
- Comandos disponibles
- Flujo de trabajo
- Arquitectura del sistema
- Configuración avanzada
