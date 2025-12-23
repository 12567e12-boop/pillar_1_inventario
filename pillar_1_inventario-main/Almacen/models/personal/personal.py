from django.db import models
import os

def renombrar_foto_empleado(instance, filename):
    nombre_archivo = instance.nombre.replace(" ", "_").lower()
    id_empleado = instance.id
    return f'empleados/{nombre_archivo}_exp_{id_empleado}.jpeg'

class Empleado(models.Model):
    # Opciones para el rol del empleado
    ROL_CHOICES = [
        ('temporal', 'Temporal'),
        ('general', 'General'),
        ('chofer', 'Chofer'),
        ('bodeguero', 'Bodeguero'),
        ('supervisor', 'Supervisor'),
        ('directivo', 'Directivo'),
    ]
    
    nombre = models.CharField(max_length=50, unique=True)
    foto = models.ImageField(upload_to=renombrar_foto_empleado, blank=True, null=True)
    puesto = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='general',
        help_text='Rol o nivel del empleado en la organización'
    )
    direccion = models.CharField(max_length=200, blank=True, null=True)
    nss = models.CharField(max_length=50, blank=True, null=True)
    tel = models.CharField(max_length=50, blank=True, null=True)
    tel_emg = models.CharField(max_length=50, blank=True, null=True)
    gafete_pdf = models.FileField(upload_to="gafetes/", blank=True, null=True)
    telegram_id = models.CharField(max_length=50, blank=True, null=True, help_text='ID de Telegram del usuario para notificaciones')

    def __str__(self):
        return self.nombre
    
    def es_supervisor(self):
        """Verifica si el empleado es supervisor o directivo"""
        return self.rol in ['supervisor', 'directivo']
    
    def es_directivo(self):
        """Verifica si el empleado es directivo"""
        return self.rol == 'directivo'
    
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['nombre']

