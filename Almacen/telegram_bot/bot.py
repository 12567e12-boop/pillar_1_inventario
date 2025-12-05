"""
Configuración principal del bot de Telegram.
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from django.conf import settings

from .handlers import (
    start_command,
    help_command,
    callback_handler,
    message_handler,
    photo_handler,
)
from .requisiciones.handlers_requisiciones import (
    nueva_requisicion_command,
    mis_requisiciones_command,
    ver_requisicion_command,
    aprobar_command,
    rechazar_command,
)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Clase principal para gestionar el bot de Telegram."""
    
    def __init__(self, token: str):
        """
        Inicializa el bot con el token proporcionado.
        
        Args:
            token: Token del bot de Telegram
        """
        self.token = token
        self.application = None
    
    def setup_handlers(self):
        """Configura todos los handlers del bot."""
        if not self.application:
            raise ValueError("La aplicación no ha sido inicializada")
        
        # Comandos básicos
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        
        # Comandos de requisiciones
        self.application.add_handler(CommandHandler("nueva", nueva_requisicion_command))
        self.application.add_handler(CommandHandler("mis_requisiciones", mis_requisiciones_command))
        self.application.add_handler(CommandHandler("ver", ver_requisicion_command))
        
        # Comandos de autorización
        self.application.add_handler(CommandHandler("aprobar", aprobar_command))
        self.application.add_handler(CommandHandler("rechazar", rechazar_command))
        
        # Callback queries (botones inline)
        self.application.add_handler(CallbackQueryHandler(callback_handler))
        
        # Mensajes de texto (para conversaciones)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        # Mensajes de fotos (para requisiciones)
        self.application.add_handler(
            MessageHandler(filters.PHOTO, photo_handler)
        )
        
        logger.info("Handlers configurados correctamente")
    
    async def post_init(self, application: Application):
        """Callback ejecutado después de inicializar la aplicación."""
        logger.info("Bot inicializado correctamente")
    
    async def post_shutdown(self, application: Application):
        """Callback ejecutado al cerrar la aplicación."""
        logger.info("Bot detenido")
    
    def run(self):
        """Inicia el bot en modo polling."""
        # Crear la aplicación
        self.application = Application.builder().token(self.token).build()
        
        # Configurar callbacks
        self.application.post_init = self.post_init
        self.application.post_shutdown = self.post_shutdown
        
        # Configurar handlers
        self.setup_handlers()
        
        # Iniciar el bot
        logger.info("Iniciando bot de Telegram...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def get_bot_token():
    """
    Obtiene el token del bot desde la configuración de Django.
    
    Returns:
        str: Token del bot
    
    Raises:
        ValueError: Si el token no está configurado
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN no está configurado en settings.py. "
            "Agrega: TELEGRAM_BOT_TOKEN = 'tu_token_aqui'"
        )
    return token


def start_bot():
    """Función principal para iniciar el bot."""
    try:
        token = get_bot_token()
        bot = TelegramBot(token)
        bot.run()
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")
        raise
