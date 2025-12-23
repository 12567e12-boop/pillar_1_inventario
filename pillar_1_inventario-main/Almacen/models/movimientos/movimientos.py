from django.db import models
from django.conf import settings

class Inventario(models.Model):
    bloque = models.ForeignKey("Bloque", on_delete=models.CASCADE)
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)
    cantidad = models.FloatField(default=0.0)
    def __str__(self): return f"{self.producto} x{self.cantidad}"
    class Meta: unique_together = (('bloque', 'producto'),)

class Registro(models.Model):
    tipo_choices = ((1, 'Entrada'), (0, 'Salida'), (-1, 'Prestado'))
    bloque = models.ForeignKey("Bloque", on_delete=models.CASCADE)
    empleado = models.ForeignKey("Empleado", on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)
    cantidad = models.FloatField(default=0.0)
    tipo = models.IntegerField(choices=tipo_choices, default=1)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self): return f"{self.empleado}: {self.producto} x{self.cantidad}"
    class Meta: permissions = [("can_use_register_form", "Can use the product in/out register form")]

class PrestamoDevuelto(models.Model):
    bloque = models.ForeignKey("Bloque", on_delete=models.CASCADE)
    empleado = models.ForeignKey("Empleado", on_delete=models.CASCADE)
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)
    cantidad = models.FloatField(default=0.0)
    fecha_entregado = models.DateField()
    entregado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prestamos_entregados')
    fecha_recibido = models.DateField(auto_now_add=True)
    recibido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prestamos_recibidos')
    def __str__(self): return f"{self.empleado}: {self.producto} x{self.cantidad}"
    class Meta: verbose_name_plural = 'prestamos devueltos'

class Transferencia(models.Model):
    tipo_choices = ((1, 'Permanente'), (0, 'Temporal'), (-1, 'Retornado'))
    bloque_origen = models.ForeignKey("Bloque", on_delete=models.CASCADE, related_name='transferencia_origen_set')
    bloque_destino = models.ForeignKey("Bloque", on_delete=models.CASCADE, related_name='transferencia_destino_set')
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)
    cantidad = models.FloatField(default=0.0)
    tipo = models.IntegerField(choices=tipo_choices, default=1)
    fecha_transferido = models.DateField(auto_now_add=True)
    transferido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transferido_usuario_set')
    fecha_retornado = models.DateField(null=True, blank=True)
    retornado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retornado_usuario_set', null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    def __str__(self): return f"{self.producto} ({self.bloque_origen}-{self.bloque_destino})"
