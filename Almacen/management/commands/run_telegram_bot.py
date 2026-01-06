"""
Comando de Django para ejecutar el bot de Telegram.

Uso:
    python manage.py run_telegram_bot
"""
import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Inicia el bot de Telegram para gestión de requisiciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            help='Token del bot de Telegram (opcional, usa TELEGRAM_BOT_TOKEN de settings)',
        )

    def handle(self, *args, **options):
        """Ejecuta el bot de Telegram."""
        self.stdout.write(self.style.SUCCESS('Iniciando bot de Telegram...'))
        
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Inventario.settings')
        django.setup()
        
        # Importar después de configurar Django
        from Almacen.telegram_bot.bot import start_bot, get_bot_token
        
        # Verificar token
        try:
            if options['token']:
                # Usar token proporcionado por argumento
                os.environ['TELEGRAM_BOT_TOKEN'] = options['token']
                self.stdout.write(
                    self.style.WARNING('Usando token proporcionado por argumento')
                )
            else:
                # Verificar que existe en settings
                token = get_bot_token()
                self.stdout.write(
                    self.style.SUCCESS(f'Token encontrado en settings')
                )
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            self.stdout.write(
                self.style.WARNING(
                    '\nPara configurar el token, agrega en settings.py:\n'
                    'TELEGRAM_BOT_TOKEN = "tu_token_aqui"\n\n'
                    'O usa: python manage.py run_telegram_bot --token "tu_token"'
                )
            )
            return
        
        # Iniciar el bot
        try:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n' + '='*60 + '\n'
                    '  Bot de Telegram - Sistema de Requisiciones\n'
                    '='*60 + '\n'
                    'El bot está activo y esperando mensajes...\n'
                    'Presiona Ctrl+C para detener el bot.\n'
                    '='*60 + '\n'
                )
            )
            
            start_bot()
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n\nBot detenido por el usuario.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError al ejecutar el bot: {e}')
            )
            raise
