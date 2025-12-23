"""
Modelo para vincular usuarios de Telegram con empleados del sistema.
"""
from django.db import models
from django.contrib.auth.models import User
from .personal.personal import Empleado


class TelegramUser(models.Model):
    """
    Modelo que vincula un usuario de Telegram con un empleado del sistema.

    Permite identificar a los usuarios que interactúan con el bot de Telegram
    y asociarlos con empleados registrados en el sistema.
    """

    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID de Telegram",
        help_text="ID único del usuario en Telegram"
    )

    username = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Username de Telegram",
        help_text="Nombre de usuario en Telegram (@username)"
    )

    first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre",
        help_text="Nombre del usuario en Telegram"
    )

    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Apellido",
        help_text="Apellido del usuario en Telegram"
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Empleado",
        help_text="Empleado asociado a este usuario de Telegram"
    )

    usuario_django = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario Django",
        help_text="Usuario de Django asociado"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
        help_text="Fecha en que se registró el usuario"
    )

    fecha_ultimo_acceso = models.DateTimeField(
        auto_now=True,
        verbose_name="Último acceso",
        help_text="Fecha del último acceso al bot"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el usuario está activo en el bot"
    )

    class Meta:
        verbose_name = "Usuario de Telegram"
        verbose_name_plural = "Usuarios de Telegram"
        ordering = ['-fecha_ultimo_acceso']

    def __str__(self):
        nombre_completo = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if nombre_completo:
            return f"{nombre_completo} ({self.telegram_id})"
        return f"Usuario {self.telegram_id}"

    @property
    def nombre_completo_telegram(self):
        """
        Retorna el nombre completo del usuario en Telegram.
        """
        partes = [self.first_name, self.last_name]
        return " ".join(filter(None, partes)).strip() or f"Usuario {self.telegram_id}"

    @classmethod
    def obtener_o_crear(cls, telegram_id, username=None, first_name=None, last_name=None):
        """
        Obtiene o crea un usuario de Telegram.

        Args:
            telegram_id: ID del usuario en Telegram
            username: Username de Telegram
            first_name: Nombre
            last_name: Apellido

        Returns:
            Tuple: (usuario, creado)
        """
        usuario, creado = cls.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        # Actualizar información si cambió
        if not creado:
            actualizar = False
            if username and usuario.username != username:
                usuario.username = username
                actualizar = True
            if first_name and usuario.first_name != first_name:
                usuario.first_name = first_name
                actualizar = True
            if last_name and usuario.last_name != last_name:
                usuario.last_name = last_name
                actualizar = True

            if actualizar:
                usuario.save()

        return usuario, creado

    def actualizar_acceso(self):
        """
        Actualiza la fecha del último acceso.
        """
        self.save(update_fields=['fecha_ultimo_acceso'])

    def vincular_empleado(self, empleado):
        """
        Vincula este usuario con un empleado.

        Args:
            empleado: Instancia del modelo Empleado
        """
        self.empleado = empleado
        self.save()

    def desvincular_empleado(self):
        """
        Desvincula al empleado actual.
        """
        self.empleado = None
        self.save()
