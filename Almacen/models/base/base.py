from django.db import models

class Unidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.nombre
    class Meta: verbose_name_plural = 'unidades'

class Producto(models.Model):
    ESPECIALIDAD_CHOICES = [
        ('plomeria', 'Plomería'),
        ('electricidad', 'Electricidad'),
        ('obra_civil', 'Obra Civil'),
        ('pintura_tablaroca', 'Pintura y Tablaroca'),
        ('vidrio_canceleria', 'Vidrio y Canceleria'),
        ('herreria', 'Herrería'),
        ('herramienta', 'Herramienta'),
        ('limpieza', 'Limpieza'),
        ('consumible', 'Consumible'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    unidad = models.ForeignKey("Unidad", on_delete=models.CASCADE)
    herramienta = models.BooleanField(default=False)
    especialidad = models.CharField(
        max_length=50, 
        choices=ESPECIALIDAD_CHOICES, 
        default='consumible',
        help_text='Seleccione la especialidad del producto. Si es una herramienta, se establecerá automáticamente.'
    )
    alerta = models.FloatField(default=0.0)
    
    def save(self, *args, **kwargs):
        # Si la especialidad es 'herramienta', establecer el booleano a True
        if self.especialidad == 'herramienta':
            self.herramienta = True
        else:
            self.herramienta = False
        super().save(*args, **kwargs)
    
    def __str__(self): 
        return self.nombre

class Bloque(models.Model):
    nombre = models.CharField(max_length=35, unique=True)
    def __str__(self): return self.nombre
