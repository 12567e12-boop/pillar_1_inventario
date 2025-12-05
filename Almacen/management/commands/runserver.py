"""
Comando personalizado de Django para ejecutar el servidor con el bot de Telegram integrado.

Uso:
    python manage.py runserver
"""
import threading
import time
from django.core.management.commands.runserver import Command as BaseRunserverCommand
from django.conf import settings


class Command(BaseRunserverCommand):
    help = 'Inicia el servidor de Django con el bot de Telegram integrado'

    def handle(self, *args, **options):
        """Ejecuta el servidor y el bot en paralelo."""
        # Iniciar el servidor en un hilo separado
        server_thread = threading.Thread(target=self._run_server, args=(args, options))
        server_thread.daemon = True
        server_thread.start()

        # Esperar un momento para que el servidor inicie
        time.sleep(2)

        # Iniciar el bot en el hilo principal
        self._run_bot()

    def _run_server(self, args, options):
        """Ejecuta el servidor Django."""
        super().handle(*args, **options)

    def _run_bot(self):
        """Ejecuta el bot de Telegram."""
        try:
            # Importar aquí para evitar problemas de configuración
            from Almacen.telegram_bot.bot import start_bot
            self.stdout.write(
                self.style.SUCCESS('Iniciando bot de Telegram...')
            )
            start_bot()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al iniciar el bot: {e}')
            )
            raise
