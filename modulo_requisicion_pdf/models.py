# Copia de empleados/models.py (solo clases relevantes)
import uuid
from django.db import models
from django.utils import timezone

class Requisicion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    obra = models.CharField(max_length=200)
    ubicacion = models.CharField(max_length=200)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    solicitante_nombre = models.CharField(max_length=200, blank=True, null=True)
    supervisor = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='requisiciones_supervisoradas'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    token_publico = models.UUIDField(
        'Token Público',
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    numero_de_articulos = models.IntegerField(null=True, blank=True)
    fecha_soli = models.DateField(null=True, blank=True, default=timezone.now)
    fecha_util = models.DateField(null=True, blank=True)
    fecha_surt = models.DateField(null=True, blank=True)
    contratista_soli = models.CharField(max_length=200, blank=True)
    contratista_auto = models.CharField(max_length=200, blank=True)
    area_util = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_hora_creacion = models.DateTimeField(default=timezone.now)
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisiciones_creadas'
    )
    def save(self, *args, **kwargs):
        # Generar ID si no existe
        if not self.id:
            obra_part = (self.obra[:4].upper() if self.obra else 'XXXX')[:4].ljust(4, 'X')
            contratista_part = (self.contratista_auto[:3].upper() if self.contratista_auto else 'XXX')[:3].ljust(3, 'X')
            fecha_part = self.fecha_soli.strftime('%Y%m%d') if self.fecha_soli else '00000000'
            self.id = f"{obra_part}{contratista_part}{fecha_part}"
        
        # Asegurar que tengamos una fecha de creación
        if not self.fecha_hora_creacion:
            self.fecha_hora_creacion = timezone.now()
            
        # Si no hay fecha de solicitud, usar la actual
        if not self.fecha_soli:
            self.fecha_soli = timezone.now().date()
            
        super().save(*args, **kwargs)
        
        # Actualizar el contador de artículos
        self.actualizar_numero_de_articulos()
    def actualizar_numero_de_articulos(self):
        self.numero_de_articulos = self.detalles.count()
        self.save(update_fields=["numero_de_articulos"])
    def __str__(self):
        return f"Requisición {self.id} - {self.obra}"

class Material(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name='materiales')
    material_id = models.CharField(max_length=50)
    tags = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    unidad = models.CharField(max_length=50)
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["requisicion__fecha_soli"]
    def __str__(self):
        return f"{self.tags} ({self.cantidad} {self.unidad})"

class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(
        Requisicion,
        related_name="detalles",
        on_delete=models.CASCADE
    )
    material_no = models.PositiveIntegerField(editable=False)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = "Detalle de requisición"
        verbose_name_plural = "Detalles de requisición"
        ordering = ["material_no"]
    def save(self, *args, **kwargs):
        if not self.material_no:
            last = (
                DetalleRequisicion.objects.filter(requisicion=self.requisicion)
                .aggregate(models.Max("material_no"))
                .get("material_no__max")
            )
            self.material_no = (last or 0) + 1
        super().save(*args, **kwargs)
        self.requisicion.actualizar_numero_de_articulos()
    def __str__(self):
        return f"Material {self.material_no}: {self.descripcion}"