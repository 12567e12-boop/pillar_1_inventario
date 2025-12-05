"""
Gestión de sesiones de usuario para el bot de Telegram.
"""
import logging
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class UserSession:
    """Gestiona las sesiones de usuario en el bot."""

    @staticmethod
    def get_user_data(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """
        Obtiene los datos de sesión del usuario.

        Args:
            context: Contexto de la conversación

        Returns:
            Dict con datos del usuario
        """
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        return context.user_data

    @staticmethod
    def set_user_data(context: ContextTypes.DEFAULT_TYPE, key: str, value: Any):
        """
        Establece un valor en la sesión del usuario.

        Args:
            context: Contexto de la conversación
            key: Clave del dato
            value: Valor a guardar
        """
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        context.user_data[key] = value

    @staticmethod
    def get_user_state(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """
        Obtiene el estado actual del usuario en la conversación.

        Args:
            context: Contexto de la conversación

        Returns:
            Estado actual o None
        """
        return UserSession.get_user_data(context).get('state')

    @staticmethod
    def set_user_state(context: ContextTypes.DEFAULT_TYPE, state: str):
        """
        Establece el estado del usuario en la conversación.

        Args:
            context: Contexto de la conversación
            state: Nuevo estado
        """
        UserSession.set_user_data(context, 'state', state)

    @staticmethod
    def clear_user_state(context: ContextTypes.DEFAULT_TYPE):
        """
        Limpia el estado del usuario.

        Args:
            context: Contexto de la conversación
        """
        if hasattr(context, 'user_data') and 'state' in context.user_data:
            del context.user_data['state']

    @staticmethod
    def get_temp_requisicion(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """
        Obtiene la requisición temporal en proceso de creación.

        Args:
            context: Contexto de la conversación

        Returns:
            Dict con datos de la requisición temporal o None
        """
        return UserSession.get_user_data(context).get('temp_requisicion')

    @staticmethod
    def set_temp_requisicion(context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]):
        """
        Establece los datos de la requisición temporal.

        Args:
            context: Contexto de la conversación
            data: Datos de la requisición
        """
        UserSession.set_user_data(context, 'temp_requisicion', data)

    @staticmethod
    def clear_temp_requisicion(context: ContextTypes.DEFAULT_TYPE):
        """
        Limpia la requisición temporal.

        Args:
            context: Contexto de la conversación
        """
        if hasattr(context, 'user_data') and 'temp_requisicion' in context.user_data:
            del context.user_data['temp_requisicion']

    @staticmethod
    def is_user_registered(context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Verifica si el usuario está registrado (tiene nombre).

        Args:
            context: Contexto de la conversación

        Returns:
            bool: True si está registrado
        """
        return UserSession.get_user_data(context).get('registered', False)

    @staticmethod
    def set_user_registered(context: ContextTypes.DEFAULT_TYPE, registered: bool = True):
        """
        Marca al usuario como registrado.

        Args:
            context: Contexto de la conversación
            registered: Estado de registro
        """
        UserSession.set_user_data(context, 'registered', registered)

    @staticmethod
    async def get_telegram_user(update: Update):
        """
        Obtiene o crea el usuario de Telegram.

        Args:
            update: Update de Telegram

        Returns:
            TelegramUser: Usuario de Telegram
        """
        from asgiref.sync import sync_to_async
        from Almacen.models.telegram_user import TelegramUser

        user = update.effective_user
        telegram_user, created = await sync_to_async(TelegramUser.obtener_o_crear)(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        # Actualizar último acceso
        await sync_to_async(telegram_user.actualizar_acceso)()

        return telegram_user
